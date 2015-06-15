from inception.argparsers.makers.maker_image import ImageMaker
from inception.constants import InceptionConstants
from inception.tools import imgtools
from dumpkey import dumppublickey
import os
import logging
import shutil
logger = logging.getLogger(__name__)
class RecoveryImageMaker(ImageMaker):
    PATH_KEYS = "res/keys"
    def __init__(self, config):
        super(RecoveryImageMaker, self).__init__(config, "recovery", InceptionConstants.OUT_NAME_RECOVERY)

    def make(self, workDir, outDir):
        # if self.getMakeConfigValue("include_update"):
        #     ramdDiskTarget = os.path.join(workDir, "recovery_ramdisk")
        #     updatezipTargetDir = os.path.join(ramdDiskTarget, "update")
        #     ramdDiskSrc = self.getMakeConfigValue("img.ramdisk")
        #     cacheDev = self.getConfig().get("cache.dev")
        #
        #     assert cacheDev, "cache.dev must be set for including update in recovery to function"
        #
        #     assert os.path.exists(os.path.join(ramdDiskSrc, "sbin", "busybox")),\
        #         "Busybox must be present in ramdisk for including update in recovery to function"
        #     shutil.copytree(ramdDiskSrc, ramdDiskTarget, symlinks=True)
        #
        #     recoveryBin = os.path.join(ramdDiskTarget, "sbin", "recovery")
        #     recoveryBinOrig = recoveryBin + ".orig"
        #     shutil.copy(recoveryBin, recoveryBinOrig)
        #
        #     os.makedirs(updatezipTargetDir)
        #     shutil.copy(os.path.join(outDir, InceptionConstants.OUT_NAME_UPDATE), updatezipTargetDir)
        #
        #     with open(recoveryBin, "w") as f:
        #         f.write("#!/sbin/busybox sh\n")
        #         f.write("mount %s /cache\n" % cacheDev)
        #         f.write("echo \"--update_package=/update/%s\" > /cache/recovery/command\n" % InceptionConstants.OUT_NAME_UPDATE)
        #         f.write("/sbin/%s\n" % os.path.basename(recoveryBinOrig))
        #
        #
        #     self.setConfigValue("recovery.img.ramdisk", ramdDiskTarget)
        #
        #     result = super(RecoveryImageMaker, self).make(workDir, outDir)
        #
        #     fsize = os.path.getsize(os.path.join(outDir, InceptionConstants.OUT_NAME_RECOVERY))
        #     maxSize = self.getMakeConfigValue("size", fsize)
        #
        #     assert fsize < maxSize, "Output recovery img is greater than max size and won't work"
        #
        #     return result
        # else:
        #     return super(RecoveryImageMaker, self).make(workDir, outDir)


        # recovery.img is str:
        #   unpack, update config with recovery data, like in bootstrap
        #   read keys
        #   gen our key, append if not exist
        #   super
        # recovery.img is dict
        #   if keys we're adding is test, warn, advice stock recovery restore, or generate own keys
        #   overwrite keys
        if self.getMakeConfigProperty("inject_keys", True):
            keysName = self.config.get("update.keys", None)
            if not keysName:
                raise ValueError("recovery.inject_keys is set to true, but update.keys is not set")
            elif keysName == "test":
                if not self.config.get("update.restore_stock_recovery"):
                    logger.warning("\n========================\n\nWARNING: You requested inception to inject 'test' keys inside the recovery image. "
                                   "It's advised to either set update.restore_stock_recovery=true or use your own keys, "
                                   "otherwise anyone can install their own update packages through the modified recovery.\n\n========================")
                else:
                    logger.warning("\n========================\n\nWARNING: You requested inception to inject 'test' keys inside the recovery image. "
                                   "It's advised to use your own keys, "
                                   "otherwise anyone can install their own update packages through the modified recovery.\n\n========================")

            signingKeysProp= self.getCommonConfigProperty("tools.signapk.keys.%s" % keysName)
            if(signingKeysProp):
                pub = signingKeysProp.getValue()["public"]
                # priv = signingKeysProp.getValue()["private"]
                pubPath = signingKeysProp.getConfig().resolveRelativePath(pub)
                # privPath = signingKeysProp.getConfig().resolveRelativePath(priv)

                keysVal = dumppublickey.print_rsa(pubPath)

                recoveryImg = self.getMakeConfigProperty("img")

                if type(recoveryImg.getValue()) is str:
                    unpackerProperty = self.config.getProperty("common.tools.unpackbootimg.bin")
                    unpacker = unpackerProperty.getConfig().resolveRelativePath(unpackerProperty.getValue())
                    with self.newTmpWorkDir() as recoveryExtractDir:
                        bootImgGenerator = imgtools.unpackimg(unpacker, recoveryImg.resolveAsRelativePath(), recoveryExtractDir)

                        if self.injectKey(os.path.join(bootImgGenerator.getRamdisk(), self.__class__.PATH_KEYS), keysVal):
                            logger.debug("injected key in %s" % self.__class__.PATH_KEYS)
                            imgType = "recovery"
                            self.setConfigValue("recovery.img", {})
                            self.setConfigValue("%s.img.cmdline" % imgType, bootImgGenerator.getKernelCmdLine(quote=False))
                            self.setConfigValue("%s.img.base" % imgType, bootImgGenerator.getBaseAddr())
                            self.setConfigValue("%s.img.ramdisk_offset" % imgType, bootImgGenerator.getRamdiskOffset())
                            self.setConfigValue("%s.img.second_offset" % imgType, bootImgGenerator.getSecondOffset())
                            self.setConfigValue("%s.img.tags_offset" % imgType, bootImgGenerator.getTagsOffset())
                            self.setConfigValue("%s.img.pagesize" % imgType, bootImgGenerator.getPageSize())
                            self.setConfigValue("%s.img.second_size" % imgType, bootImgGenerator.getSecondSize())
                            self.setConfigValue("%s.img.dt_size" % imgType, bootImgGenerator.getDeviceTreeSize())
                            self.setConfigValue("%s.img.kernel" % imgType, bootImgGenerator.getKernel())
                            self.setConfigValue("%s.img.ramdisk" % imgType, bootImgGenerator.getRamdisk())
                            self.setConfigValue("%s.img.dt" % imgType, bootImgGenerator.getDeviceTree())
                            result = super(RecoveryImageMaker, self).make(workDir, outDir)
                            self.setConfigValue("recovery.img", recoveryImg.resolveAsRelativePath())
                            return result
                        else:
                            logger.warning("key already exists in %s, not injecting" % self.__class__.PATH_KEYS)
                else:
                    with self.newTmpWorkDir() as recoveryRamDiskDir:
                        ramDiskPath = self.getMakeConfigProperty("img.ramdisk").resolveAsRelativePath()
                        if not ramDiskPath or not os.path.exists(ramDiskPath):
                            raise ValueError("Invalid valid for recovery.img.ramdisk or path does not exist: %s" % ramDiskPath)

                        ramdiskTmpDir = os.path.join(recoveryRamDiskDir, "ramdisk")
                        shutil.copytree(ramDiskPath, ramdiskTmpDir)
                        if self.injectKey(os.path.join(ramdiskTmpDir, self.__class__.PATH_KEYS), keysVal):
                            logger.debug("injected key in %s" % self.__class__.PATH_KEYS)
                            self.setConfigValue("recovery.img.ramdisk", ramdiskTmpDir)
                            result = super(RecoveryImageMaker, self).make(workDir, outDir)
                            self.setConfigValue("recovery.img.ramdisk", ramDiskPath)
                            return result
                        else:
                            logger.warning("key already exists in %s, not injecting" % self.__class__.PATH_KEYS)

        return super(RecoveryImageMaker, self).make(workDir, outDir)

    def injectKey(self, keysPath, keyData):
        with open(keysPath, 'r+') as keyfile:
            allKeys = []
            for key in keyfile.readlines():
                key = key.strip()
                key = key[:-1] if key.endswith(",") else key
                if keyData == key:
                    return False
                allKeys.append(key.strip())

            allKeys.append(keyData)
            keyfile.seek(0)
            keyfile.write(",\n".join(allKeys))

        return True
