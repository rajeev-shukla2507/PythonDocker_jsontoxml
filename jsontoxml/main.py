import os
import json
from xml.dom.minidom import parseString
import dicttoxml
import ftplib
import time
import shutil
import sys
import logging
from configparser import ConfigParser


config = ConfigParser()
config.read("./config.ini")

trgtDir=config.get("jsontoxml","trgtDir")
srcDir=config.get("jsontoxml","srcDir")
ftpServer=config.get("remote-server","ftpServer")
username=config.get("remote-server","username")
password=config.get("remote-server","password")
pingIntrvl=config.getint("jsontoxml","pingIntrvl")
pingIntrvlFTPFail=config.getint("jsontoxml","pingIntrvlFTPFail")


logging.getLogger(dicttoxml.__name__).setLevel(logging.ERROR)
log=logging.getLogger()
logging.basicConfig(filename='jsontoxml.log', filemode='w', level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p')

"""
Returns current timestamp in D<YYYYssDD>T<HHMMSS> format
input: 
output: timestamp
"""
def getTimeStamp():
    return time.strftime("D%Y%m%dT%H%M%S")

def getDateStamp():
    return time.strftime("D%Y%m%d")
"""
Creates an Archive folder, if not exists in directory and archives the filename passed append with timestamp
input: directory path, filename
output:
"""
def archiveFile(dir,filename):

    #Create a archive directory Archive id not exists
    archDirPath=os.path.join(dir,"Archive")
    if not os.path.exists(archDirPath):
        os.mkdir(archDirPath)
        log.info("Archive folder created under "+dir)

    archfilename=filename.split(".")[0]+"_"+getTimeStamp()+"."+filename.split(".")[1]
    shutil.move(os.path.join(dir,filename),os.path.join(archDirPath,archfilename))
    log.info("File "+filename+" archived as "+archfilename)

"""
Scans the dir and returns list of all the files with .<filetype> extension 
input: directory path, file type
output: list of files
"""
def scanFolderForFiles(dir,filetype):
    fileList=list()
    files=os.listdir(dir)
    for filename in files: 
        if os.path.isfile(os.path.join(dir,filename)):
            if filetype=="json":
                if filename.endswith(".json"):
                    fileList.append(filename)
            elif filetype=="xml":
                if filename.endswith(".xml"):
                    fileList.append(filename)                

    return fileList


"""
Converts json file passed to xml file
input: json filename
output: boolean conversion successful or not
"""
def jsontoXml(filename):      
    
    log.info("Processing started for json file "+filename)
    #Open file in read mode
    with open(os.path.join(srcDir,filename),'r') as file:

        try:
            json_object = json.load(file)
        except ValueError as e:
            log.warning(filename +" is not a valid json file")
            return False
            
                
        log.info("Converting file "+filename)
        xml_object=dicttoxml.dicttoxml(json_object,attr_type=False)
        outObj=parseString(xml_object).toprettyxml()
        extFileName= filename.split(".")[0]

        #Create .xml file with filename(same as input file) + TimeStamp
        genFileName=extFileName+".xml"
        outFilePath=os.path.join(trgtDir,genFileName)
        outFile=open(outFilePath,'w')
        log.info("Writing xml output for file "+filename+" in file "+genFileName)
        outFile.write(outObj)
        outFile.close()
        return True



"""
Closes the ftp connection
input: 
output:
"""
def closeConnection(cntnFtp):
    cntnFtp.close() 



def directory_exists(ftp_server,dir) :
    filelist = []
    ftp_server.retrlines('LIST',filelist.append)
    for f in filelist:
        if f.split()[-1] == dir and f.upper().startswith('D'):
            return True
    return False


def transferAllFiles(xmlfilenames):
    #get ftp connection
    ftpConnection=ftplib.FTP()
    try:
        ftpConnection.connect(ftpServer)
        log.info("Successfully connected to ftp server: "+ftpServer)
    except ftplib.all_errors as e:
        log.critical("FTP connection to server "+ftpServer+":FAILED. Retrying in "+str(config.getint("jsontoxml","pingIntrvlFTPFail"))+" seconds")
        return False
           
    #Login to ftp server
    try:
        ftpConnection.login(username,password)
        log.info("Successfully logged in to ftp server: "+ftpServer)
    except ftplib.all_errors as e:
        log.error("Login to ftp server "+ftpServer+" FAILED for user: "+username+". Username or Password may be incorrect")
        sys.exit()
        
    ftpConnection.set_pasv(True)
                  
    if directory_exists(ftpConnection,getDateStamp()) is False: 
        ftpConnection.mkd(getDateStamp())

    # Loop through each xml file, ftp  and archive
    for filename in xmlfilenames:
        with open(os.path.join(trgtDir,filename),'rb') as file:
            try:
                ftpFileName= filename.split(".")[0]+"_"+getTimeStamp()+"."+filename.split(".")[1]
                ftpConnection.storbinary("STOR /"+getDateStamp()+"/"+ ftpFileName,file)           
                log.info("File "+filename+" transferered to server "+ftpServer +" as "+ ftpFileName)
            except ftplib.all_errors as e:
                log.critical("Failed to transfer File "+filename+". Retrying in "+str(config.getint("jsontoxml","pingIntrvlFTPFail"))+" seconds. Check the destination file path ")
                return False
        # if file succesfully transferred, Archive the xml file
        archiveFile(trgtDir,filename)
    ftpConnection.close() 
    
    
    return True        


if __name__ == "__main__":
 
 while True:
        time.sleep(pingIntrvl)

        #List through all the files under source folder and process only json files
        jsonfilenames=scanFolderForFiles(srcDir,"json")

        if len(jsonfilenames) > 0: 
            # Loop through each json file. Convert to xml and save in target folder
           
            log.info("JSON files "+", ".join(jsonfilenames)+" added to source directory "+srcDir)
            for filename in jsonfilenames:
                isFileProcessed=jsontoXml(filename) 

                if  isFileProcessed is False:
                    errFileName=filename.split(".")[0]+"_NotProcessedDueToError."+filename.split(".")[1]
                    os.rename(os.path.join(srcDir,filename),os.path.join(srcDir,errFileName))
                    log.info("File "+filename+" gave error while processing. Renamed to file "+errFileName)
                    filename=errFileName
                
                # Archive all input json files
                archiveFile(srcDir,filename)

        #List through all the files under target folder and get only xml files
        xmlfilenames=scanFolderForFiles(trgtDir,"xml")

        if len(xmlfilenames) > 0:
            log.info("XML files "+", ".join(jsonfilenames)+" found in target directory "+trgtDir)
            
            isFileTransferred=transferAllFiles(xmlfilenames)            
            if isFileTransferred is False:
                pingIntrvl = config.getint("jsontoxml","pingIntrvlFTPFail")                   
            else:
                pingIntrvl = config.getint("jsontoxml","pingIntrvl")                  