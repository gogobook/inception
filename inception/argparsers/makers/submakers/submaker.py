import abc
class Submaker(object):
    __metaclass__ = abc.ABCMeta
    def __init__(self, maker, key):
        self.maker = maker
        self.key = key

    def getMaker(self):
        return self.maker

    @abc.abstractmethod
    def make(self, workDir):
        pass

    def getFSPath(self):
        return self.maker.getFSPath()

    def getCommonConfigValue(self, key, default = None):
        return self.getMaker().getCommonConfigValue(key, default)

    def getCommonConfigProperty(self, key, default = None):
        return self.getMaker().getCommonConfigProperty(key, default)

    def getConfigValue(self, key, default = None, directOnly = False):
        if not self.key == ".":
            key = self.key + "." + key if not key == "." else self.key
        return self.maker.getMakeConfigValue(key, default, directOnly)

    def getConfigProperty(self, key, default = None, directOnly = False):

        if not self.key == ".":
            key = self.key + "." + key if not key == "." else self.key
        return self.maker.getMakeConfigProperty(key, default, directOnly)

    def setConfigValue(self, key, value):
        return self.maker.setConfigValue(key, value)