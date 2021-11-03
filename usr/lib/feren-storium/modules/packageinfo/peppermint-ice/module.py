import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import json
import locale


def should_load(): #Should this module be loaded?
    return True


class IceInfoModuleException(Exception): # Name this according to the module to allow easier debugging
    pass



class main():

    def __init__(self, storebrain):

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")

        #Name to be used in Debugging output
        self.title = _("Ice Website Information Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Ice Website Information")
        
        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        
        #What package types does this provide info for?
        self.types_provided = ["peppermint-ice"]
        
        #Information Storage to keep it in - modify list as appropriate for files
        self.json_storage = {}
        
        #Lock to keep stuff from happening while memory is refreshing
        self.memory_refreshing = False
        
        #Locale (for info modules)
        self.locale = locale.getlocale()[0]
        
        #Force a memory refresh
        self.refresh_memory()
        
        #Package IDs List
        self.pkg_ids = []
        #Package Categories - IDs List
        self.pkg_categoryids = {}
        
        
    def build_ids_list(self): #Build list of package IDs
        self.pkg_ids = []
        for i in [self.json_storage["package-info/peppermint-ice"]]:
            try:
                for package in i:
                    if package not in self.pkg_ids:
                        self.pkg_ids.append(package)
            except:
                pass
        
    def build_categories_ids(self): #Build categories list for package IDs
        self.pkg_categoryids = {}
        #Do nothing else as this isn't a generic module
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
        
        self.json_storage = {}
        
        for i in ["package-info/peppermint-ice"]:
            with open("/usr/share/feren-storium/curated/" + i + "/data.json", 'r') as fp:            
                self.json_storage[i] = json.loads(fp.read())
        
        self.memory_refreshing = False
                
        
    def getPackageJSON(self):
        #Return a json of all package names
        packagejson = {}
        for i in [self.json_storage["package-info/peppermint-ice"]]:
            try:
                packagejson.update(i)
            except:
                pass
        return packagejson
      
    
    def getInfo(self, packagename, packagetype):
        #Get information on a package using the JSON data
        
        if packagetype not in self.types_provided:
            raise IceInfoModuleException(packagetype, _("is not supported by this information module. If you are getting an exception throw, it means you have not used a Try to respond to the module not supporting this type of package."))
            return
        
        #General in-Store stuff
        shortdescription = self.getShortDescription(packagename)
        author = self.getAuthor(packagename)
        bugsurl = self.getBugsURL(packagename)
        tosurl = self.getTOSURL(packagename)
        privpolurl = self.getPrivPolURL(packagename)
        
        #Ice-specific stuff
        keywords = self.getKeywords(packagename)
        
        extrasids = self.getExtrasIDs(packagename)
        realnameextras = self.getExtraRealNames(packagename)
        iconuriextras = self.getIconURIExtras(packagename)
        websiteextras = self.getWebsiteExtras(packagename)
        keywordsextras = self.getKeywordsExtras(packagename)
        
        
        #Return values
        return {"author": author, "bugreporturl": bugsurl, "tosurl": tosurl, "privpolurl": privpolurl, "keywords": keywords, "shortdescription": shortdescription, "extrasids": extrasids, "realnameextras": realnameextras, "iconuriextras": iconuriextras, "websiteextras": websiteextras, "keywordsextras": keywordsextras}
        

    def getShortDescription(self, packagename):
        try:
            shortdescription = self.json_storage["package-info/peppermint-ice"][packagename]["shortdescription"]
        except:
            shortdescription = _("Website Application")
        return shortdescription
    
    def getKeywords(self, packagename):
        try:
            keywords = self.json_storage["package-info/peppermint-ice"][packagename]["keywords"]
        except:
            raise IceInfoModuleException(packagename, _("has no keywords value in the package metadata. Websites MUST have keywords values when curated."))
            return
        return keywords
    
    def getAuthor(self, packagename):
        try:
            author = self.json_storage["package-info/peppermint-ice"][packagename]["author"]
        except:
            author = _("Unknown Author")
        return author
      
    def getBugsURL(self, packagename):
        try:
            bugsurl = self.json_storage["package-info/peppermint-ice"][packagename]["bugreporturl"]
        except:
            bugsurl = ""
        return bugsurl
      
    def getTOSURL(self, packagename):
        try:
            tosurl = self.json_storage["package-info/peppermint-ice"][packagename]["tos"]
        except:
            tosurl = ""
        return tosurl
      
    def getPrivPolURL(self, packagename):
        try:
            privpolurl = self.json_storage["package-info/peppermint-ice"][packagename]["privpol"]
        except:
            privpolurl = ""
        return privpolurl
      
    def getExtrasIDs(self, packagename):
        try:
            extrasids = self.json_storage["package-info/peppermint-ice"][packagename]["extrasids"]
        except:
            extrasids = []
        return extrasids
      
    def getExtraRealNames(self, packagename):
        try:
            realnameextras = self.json_storage["package-info/peppermint-ice"][packagename]["realnameextras"]
        except:
            realnameextras = []
        return realnameextras
      
    def getIconURIExtras(self, packagename):
        try:
            iconuriextras = self.json_storage["package-info/peppermint-ice"][packagename]["iconuriextras"]
        except:
            iconuriextras = []
        return iconuriextras
      
    def getWebsiteExtras(self, packagename):
        try:
            websiteextras = self.json_storage["package-info/peppermint-ice"][packagename]["websiteextras"]
        except:
            websiteextras = []
        return websiteextras
      
    def getKeywordsExtras(self, packagename):
        try:
            keywordsextras = self.json_storage["package-info/peppermint-ice"][packagename]["keywordsextras"]
        except:
            keywordsextras = []
        return keywordsextras


if __name__ == "__main__":
    module = PackageInfoModule()