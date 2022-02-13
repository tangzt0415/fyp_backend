import os
import zipfile
import io
import os , os.path
import math
import time
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from fastapi.responses import Response
from typing import List
import uvicorn
#.\env\Scripts\activate

# TODO:

# downsample images, take first pixel and jump to third. (1 to 2 down sampling)

# - compare speed and quality! 
app = FastAPI()

students = {
    1:{
        "name": "john"
    },
    2:{
        "name": "tom"
    }
}

    # Pass the arguments of the function as parameters in the command line code
binPath = r"C:\Users\TANG\Downloads\Meshroom-2021.1.0-win64\Meshroom-2021.1.0\aliceVision\bin" #sys.argv[1]           ##  --> path of the binary files from Meshroom
baseDir = r"C:\Users\TANG\Desktop\FYP\meshroom_CLI\output" # sys.argv[2]           ##  --> name of the Folder containing the process (a new folder will be created)
imgDir = r"C:\Users\TANG\Desktop\FYP\meshroom_CLI\input"#sys.argv[3]            ##  --> Folder containing the images 

@app.get("/get_obj")
def index():
    return FileResponse(r"C:\Users\TANG\Desktop\FYP\meshroom_CLI\output\adidas_hole\texturedMesh.obj")

@app.get("/get_zip")
def index2():
    #works but not with docs
    #shutil.make_archive('output', 'zip', r'C:\Users\TANG\Desktop\FYP\meshroom_CLI\output\13_Texturing')
    shutil.make_archive('output', 'zip', r'C:\Users\TANG\Desktop\FYP\meshroom_CLI\output')
    zipped_file = r"C:\Users\TANG\Desktop\FYP\meshroom_CLI\output.zip"
    s = io.BytesIO()
    response = FileResponse(zipped_file)
    return response

@app.get("/emptyOutput")
def deleteOutput():
    folder = clearDirectory(baseDir)
    return "folder removed: " + folder

@app.get("/emptyInput")
def deleteInput():
    folder = clearDirectory(imgDir)
    return "folder removed: " + folder


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    with open(f'{file.filename}','wb') as buffer:
        shutil.copyfileobj(file.file, buffer)
    buffer.close()
    return {"file_name":file.filename}

@app.post("/upload_zip")
async def z_upload(file: UploadFile = File(...)):
    with open(f'{file.filename}','wb') as buffer:
        shutil.copyfileobj(file.file, buffer)
        shutil.unpack_archive(file.filename, imgDir)
    buffer.close()
    remove(file.filename)
    return {"file_name":file.filename}

@app.post("/m_upload")
async def m_upload(files: List[UploadFile] = File(...)):
    file_list = []
    for img in files:
        file_list.append(str(img.filename))
        with open(f'{img.filename}','wb') as buffer:
            shutil.copyfileobj(img.file, buffer)
        
        shutil.move(img.filename, imgDir) 

    return {"MultiUploadfinished -> file_list":file_list}     

@app.get("/run_main")
def run_main():
    main()
    return "done"


dirname = os.path.dirname(os.path.abspath(__file__))  # Absolute path of this file
verboseLevel = "\"" + "error" + "\""  # detail of the logs (error, info, etc)


def clearDirectory(path):
    folder = path
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    return path


    

# def zipfiles(filenames):
#     zip_filename = "archive.zip"

#     s = io.BytesIO()
#     zf = zipfile.ZipFile(s, "w")

#     for fpath in filenames:
#         # Calculate path for file in zip
#         fdir, fname = os.path.split(fpath)

#         # Add file, at correct path
#         zf.write(fpath, fname)

#     # Must close zip for all contents to be written
#     zf.close()

#     # Grab ZIP file from in-memory, make response with correct MIME-type
#     resp = Response(s.getvalue(), media_type="application/x-zip-compressed", headers={
#         'Content-Disposition': f'attachment;filename={zip_filename}'
#     })

#     return resp

def SilentMkdir(theDir):    # function to create a directory
    try:
        os.mkdir(theDir)
    except:
        pass
    return 0

def remove(path):
    """ param <path> could either be relative or absolute. """
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)  # remove the file
    elif os.path.isdir(path):
        shutil.rmtree(path)  # remove dir and all contains
    else:
        raise ValueError("file {} is not a file or dir.".format(path))

def run_1_cameraInit(binPath,baseDir,imgDir):

    taskFolder = "/1_CameraInit"
    SilentMkdir(baseDir + taskFolder)

    print("----------------------- 1/13 CAMERA INITIALIZATION -----------------------")

    imageFolder = "\"" + imgDir + "\""
    sensorDatabase = "\""+ str(Path(binPath).parent) + "\\share\\aliceVision\\cameraSensors.db" "\"" # Path to the sensors database, might change in later versions of meshrrom
   
    output = "\"" + baseDir + taskFolder + "/cameraInit.sfm" + "\""

    cmdLine = binPath + "\\aliceVision_cameraInit.exe"
    cmdLine += " --imageFolder {0} --sensorDatabase {1} --output {2}".format(
        imageFolder, sensorDatabase, output)

    cmdLine += " --defaultFieldOfView 45" 
    cmdLine += " --allowSingleView 1"
    cmdLine += " --verboseLevel " + verboseLevel

    print(cmdLine)
    os.system(cmdLine)

    return 0


def run_2_featureExtraction(binPath,baseDir , numberOfImages , imagesPerGroup=40):

    taskFolder = "/2_FeatureExtraction"
    SilentMkdir(baseDir + taskFolder)

    print("----------------------- 2/13 FEATURE EXTRACTION -----------------------")

    _input = "\"" + baseDir + "/1_CameraInit/cameraInit.sfm" + "\""
    output = "\"" + baseDir + taskFolder + "\""

    cmdLine = binPath + "\\aliceVision_featureExtraction"
    cmdLine += " --input {0} --output {1}".format(_input, output)
    cmdLine += " --forceCpuExtraction 1"


    #when there are more than 40 images, it is good to send them in groups
    if(numberOfImages>imagesPerGroup):
        numberOfGroups=int(math.ceil( numberOfImages/imagesPerGroup))
        for i in range(numberOfGroups):
            cmd=cmdLine + " --rangeStart {} --rangeSize {} ".format(i*imagesPerGroup,imagesPerGroup)
            print("------- group {} / {} --------".format(i+1,numberOfGroups))
            print(cmd)
            os.system(cmd)

    else:
        print(cmdLine)
        os.system(cmdLine)


def run_3_imageMatching(binPath,baseDir):

    taskFolder = "/3_ImageMatching"
    SilentMkdir(baseDir + taskFolder)

    print("----------------------- 3/13 IMAGE MATCHING -----------------------")

    _input = "\"" + baseDir + "/1_CameraInit/cameraInit.sfm" + "\""
    featuresFolders = "\"" + baseDir + "/2_FeatureExtraction" + "\""
    output = "\"" + baseDir + taskFolder + "/imageMatches.txt" + "\""

    cmdLine = binPath + "\\aliceVision_imageMatching.exe"
    cmdLine += " --input {0} --featuresFolders {1} --output {2}".format(
        _input, featuresFolders, output)

    cmdLine +=  " --tree " + "\""+ str(Path(binPath).parent)+ "/share/aliceVision/vlfeat_K80L3.SIFT.tree\""
    cmdLine += " --verboseLevel " + verboseLevel

    print(cmdLine)
    os.system(cmdLine)


def run_4_featureMatching(binPath,baseDir,numberOfImages,imagesPerGroup=20):

    taskFolder = "/4_featureMatching"
    SilentMkdir(baseDir + taskFolder)

    print("----------------------- 4/13 FEATURE MATCHING -----------------------")

    _input = "\"" +   baseDir + "/1_CameraInit/cameraInit.sfm" + "\""
    output = "\""  + baseDir + taskFolder + "\""
    featuresFolders = "\"" +  baseDir + "/2_FeatureExtraction" + "\""
    imagePairsList = "\"" +  baseDir + "/3_ImageMatching/imageMatches.txt" + "\""

    cmdLine = binPath + "\\aliceVision_featureMatching.exe"
    cmdLine += " --input {0} --featuresFolders {1} --output {2} --imagePairsList {3}".format(
        _input, featuresFolders, output, imagePairsList)

    cmdLine += " --knownPosesGeometricErrorMax 5"
    cmdLine += " --verboseLevel " + verboseLevel

    cmdLine += " --describerTypes sift --photometricMatchingMethod ANN_L2 --geometricEstimator acransac --geometricFilterType fundamental_matrix --distanceRatio 0.8"
    cmdLine += " --maxIteration 2048 --geometricError 0.0 --maxMatches 0"
    cmdLine += " --savePutativeMatches False --guidedMatching False --matchFromKnownCameraPoses False --exportDebugFiles True"

    #when there are more than 20 images, it is good to send them in groups
    if(numberOfImages>imagesPerGroup):
        numberOfGroups=math.ceil( numberOfImages/imagesPerGroup)
        for i in range(numberOfGroups):
            cmd=cmdLine + " --rangeStart {} --rangeSize {} ".format(i*imagesPerGroup,imagesPerGroup)
            print("------- group {} / {} --------".format(i,numberOfGroups))
            print(cmd)
            os.system(cmd)

    else:
        print(cmdLine)
        os.system(cmdLine)

def run_5_structureFromMotion(binPath,baseDir):

    taskFolder = "/5_structureFromMotion"
    SilentMkdir(baseDir + taskFolder)

    print("----------------------- 5/13 STRUCTURE FROM MOTION -----------------------")

    _input = "\"" +  baseDir + "/1_CameraInit/cameraInit.sfm" + "\""
    output = "\"" +  baseDir + taskFolder + "/sfm.abc" + "\" "
    outputViewsAndPoses = "\"" + baseDir + taskFolder + "/cameras.sfm" + "\""
    extraInfoFolder = "\""  + baseDir + taskFolder + "\""
    featuresFolders = "\"" + baseDir + "/2_FeatureExtraction" + "\""
    matchesFolders = "\"" +  baseDir + "/4_featureMatching" + "\""

    cmdLine = binPath + "\\aliceVision_incrementalSfm.exe"
    cmdLine += " --input {0} --output {1} --outputViewsAndPoses {2} --extraInfoFolder {3} --featuresFolders {4} --matchesFolders {5}".format(
        _input, output, outputViewsAndPoses, extraInfoFolder, featuresFolders, matchesFolders)

    cmdLine += " --verboseLevel " + verboseLevel

    print(cmdLine)
    os.system(cmdLine)


def run_6_prepareDenseScene(binPath,baseDir):
    taskFolder = "/6_PrepareDenseScene"
    SilentMkdir(baseDir + taskFolder)

    print("----------------------- 6/13 PREPARE DENSE SCENE -----------------------")
    _input = "\"" +  baseDir +  "/5_structureFromMotion/sfm.abc" + "\""
    output = "\"" + baseDir + taskFolder + "\" "

    cmdLine = binPath + "\\aliceVision_prepareDenseScene.exe"
    cmdLine += " --input {0}  --output {1} ".format(_input,  output)

    cmdLine += " --verboseLevel " + verboseLevel

    print(cmdLine)
    os.system(cmdLine)


def run_7_depthMap(binPath,baseDir ,numberOfImages , groupSize=6 , downscale = 2):
    taskFolder = "/7_DepthMap"
    SilentMkdir(baseDir + taskFolder)

    print("----------------------- 7/13 DEPTH MAP -----------------------")
    _input = "\""  + baseDir +   "/5_structureFromMotion/sfm.abc" + "\""
    output = "\"" + baseDir + taskFolder + "\""
    imagesFolder = "\"" + baseDir + "/6_PrepareDenseScene" + "\""

    cmdLine = binPath + "\\aliceVision_depthMapEstimation.exe"
    cmdLine += " --input {0}  --output {1} --imagesFolder {2}".format(
        _input,  output, imagesFolder)

    cmdLine += " --verboseLevel " + verboseLevel
    cmdLine += " --downscale " + str(downscale)

    
    numberOfBatches = int(math.ceil( numberOfImages / groupSize ))

    for i in range(numberOfBatches):
        groupStart = groupSize * i
        currentGroupSize = min(groupSize,numberOfImages - groupStart)
        if groupSize > 1:
            print("DepthMap Group {} of {} : {} to {}".format(i, numberOfBatches, groupStart, currentGroupSize))
            cmd = cmdLine + (" --rangeStart {} --rangeSize {}".format(str(groupStart),str(groupSize)))       
            print(cmd)
            os.system(cmd)


def run_8_depthMapFilter(binPath,baseDir):
    taskFolder = "/8_DepthMapFilter"
    SilentMkdir(baseDir + taskFolder)

    print("----------------------- 8/13 DEPTH MAP FILTER-----------------------")
    _input = "\""  + baseDir +   "/5_structureFromMotion/sfm.abc" + "\""
    output = "\"" + baseDir + taskFolder + "\""
    depthMapsFolder = "\""  + baseDir + "/7_DepthMap" + "\""

    cmdLine = binPath + "\\aliceVision_depthMapFiltering.exe"
    cmdLine += " --input {0}  --output {1} --depthMapsFolder {2}".format(
        _input,  output, depthMapsFolder)

    cmdLine += " --verboseLevel " + verboseLevel

    print(cmdLine)
    os.system(cmdLine)


def run_9_meshing(binPath,baseDir  , maxInputPoints = 50000000  , maxPoints=1000000):
    taskFolder = "/9_Meshing"
    SilentMkdir(baseDir + taskFolder)

    print("----------------------- 9/13 MESHING -----------------------")
    _input = "\""  + baseDir +  "/5_structureFromMotion/sfm.abc" + "\""
    output = "\""  + baseDir +   taskFolder + "/densePointCloud.abc" "\""
    outputMesh = "\""  + baseDir + taskFolder + "/mesh.obj" + "\""
    depthMapsFolder = "\"" + baseDir + "/8_DepthMapFilter" + "\""

    cmdLine = binPath + "\\aliceVision_meshing.exe"
    cmdLine += " --input {0}  --output {1} --outputMesh {2} --depthMapsFolder {3} ".format(
        _input,  output, outputMesh, depthMapsFolder)

    cmdLine += " --maxInputPoints " + str(maxInputPoints)
    cmdLine += " --maxPoints " + str(maxPoints)
    cmdLine += " --verboseLevel " + verboseLevel


    print(cmdLine)
    os.system(cmdLine)


def run_10_meshFiltering(binPath,baseDir ,keepLargestMeshOnly="True"):
    taskFolder = "/10_MeshFiltering"
    SilentMkdir(baseDir + taskFolder)

    print("----------------------- 10/13 MESH FILTERING -----------------------")
    inputMesh = "\""  + baseDir + "/9_Meshing/mesh.obj" + "\""
    outputMesh = "\""  + baseDir + taskFolder + "/mesh.obj" + "\""

    cmdLine = binPath + "\\aliceVision_meshFiltering.exe"
    cmdLine += " --inputMesh {0}  --outputMesh {1}".format(
        inputMesh, outputMesh)

    cmdLine += " --verboseLevel " + verboseLevel
    cmdLine += " --keepLargestMeshOnly " + keepLargestMeshOnly

    print(cmdLine)
    os.system(cmdLine)


def run_11_meshDecimate(binPath,baseDir , simplificationFactor=0.8 , maxVertices=15000):
    taskFolder = "/11_MeshDecimate"
    SilentMkdir(baseDir + taskFolder)

    print("----------------------- 11/13 MESH DECIMATE -----------------------")
    inputMesh = "\""  + baseDir + "/10_MeshFiltering/mesh.obj" + "\""
    outputMesh = "\""  + baseDir + taskFolder + "/mesh.obj" + "\""

    cmdLine = binPath + "\\aliceVision_meshDecimate.exe"
    cmdLine += " --input {0}  --output {1}".format(
        inputMesh, outputMesh)

    cmdLine += " --verboseLevel " + verboseLevel
    cmdLine += " --simplificationFactor " + str(simplificationFactor)
    cmdLine += " --maxVertices " + str(maxVertices)

    print(cmdLine)
    os.system(cmdLine)


def run_12_meshResampling(binPath,baseDir , simplificationFactor=0.8 , maxVertices=15000):
    taskFolder = "/12_MeshResampling"
    SilentMkdir(baseDir + taskFolder)

    print("----------------------- 12/13 MESH RESAMPLING -----------------------")
    inputMesh = "\"" + baseDir +  "/11_MeshDecimate/mesh.obj" + "\""
    outputMesh = "\"" + baseDir  + taskFolder + "/mesh.obj" + "\""

    cmdLine = binPath + "\\aliceVision_meshResampling.exe"
    cmdLine += " --input {0}  --output {1}".format( inputMesh, outputMesh)

    cmdLine += " --verboseLevel " + verboseLevel
    cmdLine += " --simplificationFactor " + str(simplificationFactor)
    cmdLine += " --maxVertices " + str(maxVertices)

    print(cmdLine)
    os.system(cmdLine)


def run_13_texturing(binPath , baseDir , textureSide = 4096 , downscale=4 , unwrapMethod = "Basic"):
    taskFolder = "/13_Texturing"
    SilentMkdir(baseDir + taskFolder)

    print("----------------------- 13/13 TEXTURING  -----------------------")
    _input = "\"" + baseDir +   "/9_Meshing/densePointCloud.abc" + "\""
    imagesFolder = "\""  + baseDir + "/6_PrepareDenseScene" "\""
    inputMesh = "\"" + baseDir + "/12_MeshResampling/mesh.obj" + "\""
    output = "\"" + baseDir + taskFolder + "\""

    cmdLine = binPath + "\\aliceVision_texturing.exe"
    cmdLine += " --input {0} --inputMesh {1} --output {2} --imagesFolder {3}".format(
        _input, inputMesh, output, imagesFolder)

    cmdLine += " --textureSide " + str(textureSide)
    cmdLine += " --downscale " + str(downscale)
    cmdLine += " --verboseLevel " + verboseLevel
    cmdLine += " --unwrapMethod " + unwrapMethod

    print(cmdLine)
    os.system(cmdLine)



def main():
    
#C:\Users\TANG\Desktop\FYP\meshroom_CLI\dataset_monstree-master
#C:\Users\TANG\Downloads\Meshroom-2021.1.0-win64\Meshroom-2021.1.0\aliceVision\bin
#C:\Users\TANG\Desktop\FYP\meshroom_CLI\output

    numberOfImages =  len([name for name in os.listdir(imgDir) if os.path.isfile(os.path.join(imgDir, name))])      ## number of files in the folder

    SilentMkdir(baseDir)

    startTime = time.time()

    run_1_cameraInit(binPath,baseDir,imgDir)
    run_2_featureExtraction(binPath,baseDir , numberOfImages)
    run_3_imageMatching(binPath,baseDir)
    run_4_featureMatching(binPath,baseDir,numberOfImages)
    run_5_structureFromMotion(binPath,baseDir)
    run_6_prepareDenseScene(binPath,baseDir)
    run_7_depthMap(binPath,baseDir , numberOfImages )
    run_8_depthMapFilter(binPath,baseDir)
    run_9_meshing(binPath,baseDir)
    run_10_meshFiltering(binPath,baseDir)
    run_11_meshDecimate(binPath,baseDir)
    run_12_meshResampling(binPath,baseDir)
    run_13_texturing(binPath,baseDir)

    
    print("-------------------------------- DONE ----------------------")
    endTime = time.time()
    hours, rem = divmod(endTime-startTime, 3600)
    minutes, seconds = divmod(rem, 60)
    print("time elapsed: "+"{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds))
    print("press any key to close")




# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)