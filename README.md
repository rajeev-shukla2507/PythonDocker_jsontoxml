## Task

Write a python script, which will convert json files to xml files and transfers it in a remote location.

Environment:

Python, Docker

Description:

Solution should be prepared as two Docker images, 1st to send files, and 2nd to receive them.

Deployment of these containers should be automated using docker-compose or shell script.

Python script on container A:

    1. convert all json files to xml

    2. Transfer it to a remote location (container B)

Python script on container B:

    1. Receive files

    2. Store files

So, in other words, pipeline should look like:

Json -> XML -> transfer -> XML

**Acceptance criteria**:

Any given Json putted to container A appears in XML form on container B using mentioned pipeline.

## Solution:

#### Algorithm:

1. Create a python script which performs below functionalities:
    i. Monitor the source directory for any .json file in small intervals.

        if (.json file found)
        - converts to xml
        - append time stamp to xml and save it to target directory
        - append timestamp to input json file and archive it

    ii. Monitor the target directory for any .xml file in small intervals.

        if (.xml file found) 
        - ftp it to container B(ftp server), under a folder based on current date
        - append timestamp to the xml file and archive it

#### Architecture Diagram:

![Flow Diagram] (\images\flow diagram.png)

1. Create Docker file to build image for container A, with Entry point as the python script from step 1 above.

![](Aspose.Words.1142695d-5757-4923-b137-123f6f383184.002.png)

1. Create a Docker compose file, having 2 services. One for the python script to run in Container A and other to receive the file from container A.

![](Aspose.Words.1142695d-5757-4923-b137-123f6f383184.003.png)	



**Environment** 

OS: 

`	`![](Aspose.Words.1142695d-5757-4923-b137-123f6f383184.004.png)

Python:

`	`![](Aspose.Words.1142695d-5757-4923-b137-123f6f383184.005.png)

Docker:

`	`![](Aspose.Words.1142695d-5757-4923-b137-123f6f383184.006.png)

Pip package required:

`	`![](Aspose.Words.1142695d-5757-4923-b137-123f6f383184.007.png)

**Folder structure:**

`	`![](Aspose.Words.1142695d-5757-4923-b137-123f6f383184.008.png)

**Steps:** 

1. Run sudo docker-compose up –d
1. Check the containers deployed and running

![](Aspose.Words.1142695d-5757-4923-b137-123f6f383184.009.png)

1. Copy json files under ./testdata to /home/src of jsontoxmlconvertor

sudo docker cp testdata/. jsontoxmlconvertor:/home/src

1. Xml file created and stored under the current Date folder in ftpd-server

![](Aspose.Words.1142695d-5757-4923-b137-123f6f383184.010.png)

1. Check jsontoxml.log in jsontoxmlconvertor container

![](Aspose.Words.1142695d-5757-4923-b137-123f6f383184.011.png)


1. Check the src and target archived file

![](Aspose.Words.1142695d-5757-4923-b137-123f6f383184.012.png)




