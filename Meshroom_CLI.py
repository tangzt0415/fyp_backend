from distutils import cmd
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
def get_3d_Object():
    return FileResponse(r"C:\Users\TANG\Desktop\FYP\meshroom_CLI\output\adidas_hole\texturedMesh.obj")

@app.get("/get_zip")
def get_obj_zip():
    shutil.make_archive(r'C:\Users\TANG\Desktop\FYP\meshroom_CLI\output\gen3D', 'zip', r'C:\Users\TANG\Desktop\FYP\meshroom_CLI\output\13_Texturing')
    zipped_file = r"C:\Users\TANG\Desktop\FYP\meshroom_CLI\output\gen3D.zip"
    s = io.BytesIO()
    response = FileResponse(zipped_file)
    return response

@app.get("/emptyOutput")
def delete_Output():
    folder = clearDirectory(baseDir)
    return "folder removed: " + folder

@app.get("/emptyInput")
def delete_Input():
    folder = clearDirectory(imgDir)
    return "folder removed: " + folder

@app.get("/clearServer")
def clear_Server():
    folder = clearDirectory(imgDir)
    folder = clearDirectory(baseDir)
    return "folder removed: " + folder


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    with open(f'{file.filename}','wb') as buffer:
        shutil.copyfileobj(file.file, buffer)
    buffer.close()
    return {"file_name":file.filename}

@app.post("/upload_zip")
async def zip_upload(file: UploadFile = File(...)):
    with open(f'{file.filename}','wb') as buffer:
        shutil.copyfileobj(file.file, buffer)
        shutil.unpack_archive(file.filename, imgDir)
    buffer.close()
    remove(file.filename)
    return {"file_name":file.filename}

@app.post("/m_upload")
async def multiple_upload(files: List[UploadFile] = File(...)):
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

    cmdLine += " --defaultFieldOfView 45.0" 
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
    cmdLine += " --describerTypes sift --describerPreset normal --describerQuality normal --contrastFiltering GridSort --gridFiltering True --forceCpuExtraction 1"


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
    cmdLine += " --weights "" --minNbImages 200 --maxDescriptors 500 --nbMatches 50 --verboseLevel " + verboseLevel

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

    
    cmdLine += " --verboseLevel " + verboseLevel

    cmdLine += " --describerTypes sift --photometricMatchingMethod ANN_L2 --geometricEstimator acransac --geometricFilterType fundamental_matrix --distanceRatio 0.8"
    cmdLine += " --maxIteration 2048 --geometricError 0.0 --knownPosesGeometricErrorMax 5.0 --maxMatches 0"
    cmdLine += " --savePutativeMatches False --guidedMatching False --matchFromKnownCameraPoses False --exportDebugFiles False"

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

    cmdLine += " --describerTypes sift --localizerEstimator acransac --observationConstraint Basic --localizerEstimatorMaxIterations 4096 --localizerEstimatorError 0.0 --lockScenePreviouslyReconstructed False --useLocalBA True --localBAGraphDistance 1 --maxNumberOfMatches 0 --minNumberOfMatches 0 --minInputTrackLength 2 --minNumberOfObservationsForTriangulation 2 --minAngleForTriangulation 3.0 --minAngleForLandmark 2.0 --maxReprojectionError 4.0 --minAngleInitialPair 5.0 --maxAngleInitialPair 40.0 --useOnlyMatchesFromInputFolder False --useRigConstraint True --lockAllIntrinsics False --filterTrackForks False  --interFileExtension .abc --verboseLevel " + verboseLevel

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

    cmdLine += " --outputFileType exr --saveMetadata True --saveMatricesTxtFiles False --evCorrection False --verboseLevel " + verboseLevel

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
    cmdLine += " --downscale " + str(downscale) + " --minViewAngle 2.0 --maxViewAngle 70.0 --sgmMaxTCams 10 --sgmWSH 4 --sgmGammaC 5.5 --sgmGammaP 8.0 --refineMaxTCams 6 --refineNSamplesHalf 150 --refineNDepthsToRefine 31 --refineNiters 100 --refineWSH 3 --refineSigma 15 --refineGammaC 15.5 --refineGammaP 8.0 --refineUseTcOrRcPixSize False --exportIntermediateResults False --nbGPUs 0"

    
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

    cmdLine += " --minViewAngle 2.0 --maxViewAngle 70.0 --nNearestCams 10 --minNumOfConsistentCams 3 --minNumOfConsistentCamsWithLowSimilarity 4 --pixSizeBall 0 --pixSizeBallWithLowSimilarity 0 --computeNormalMaps False --verboseLevel " + verboseLevel

    print(cmdLine)
    os.system(cmdLine)


def run_9_meshing(binPath,baseDir  , maxInputPoints = 500000 , maxPoints=100000):
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

    cmdLine += " --estimateSpaceFromSfM True --estimateSpaceMinObservations 3 --estimateSpaceMinObservationAngle 10"
    cmdLine += " --maxInputPoints " + str(maxInputPoints)
    cmdLine += " --maxPoints " + str(maxPoints)
    cmdLine += " --maxPointsPerVoxel 1000000 --minStep 2 --partitioning singleBlock --repartition multiResolution --angleFactor 15.0 --simFactor 15.0 --pixSizeMarginInitCoef 2.0 --pixSizeMarginFinalCoef 4.0 --voteMarginFactor 4.0 --contributeMarginFactor 2.0 --simGaussianSizeInit 10.0 --simGaussianSize 10.0 --minAngleThreshold 1.0 --refineFuse True --helperPointsGridSize 10 --nPixelSizeBehind 4.0 --fullWeight 1.0 --voteFilteringForWeaklySupportedSurfaces True --addLandmarksToTheDensePointCloud False --invertTetrahedronBasedOnNeighborsNbIterations 10 --minSolidAngleRatio 0.2 --nbSolidAngleFilteringIterations 2 --colorizeOutput False --maxNbConnectedHelperPoints 50 --saveRawDensePointCloud False --exportDebugTetrahedralization False --seed 0"
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

   
    # cmdLine += " --keepLargestMeshOnly " + keepLargestMeshOnly
    cmdLine += " --keepLargestMeshOnly False --smoothingSubset all --smoothingBoundariesNeighbours 0 --smoothingIterations 5 --smoothingLambda 1.0 --filteringSubset all --filteringIterations 1 --filterLargeTrianglesFactor 60.0 --filterTrianglesRatio 0.0"
    cmdLine += " --verboseLevel " + verboseLevel

    print(cmdLine)
    os.system(cmdLine)


# def run_11_meshDecimate(binPath,baseDir , simplificationFactor=0.8 , maxVertices=15000):
#     taskFolder = "/11_MeshDecimate"
#     SilentMkdir(baseDir + taskFolder)

#     print("----------------------- 11/13 MESH DECIMATE -----------------------")
#     inputMesh = "\""  + baseDir + "/10_MeshFiltering/mesh.obj" + "\""
#     outputMesh = "\""  + baseDir + taskFolder + "/mesh.obj" + "\""

#     cmdLine = binPath + "\\aliceVision_meshDecimate.exe"
#     cmdLine += " --input {0}  --output {1}".format(
#         inputMesh, outputMesh)

#     cmdLine += " --verboseLevel " + verboseLevel
#     cmdLine += " --simplificationFactor " + str(simplificationFactor)
#     cmdLine += " --maxVertices " + str(maxVertices)

#     print(cmdLine)
#     os.system(cmdLine)


# def run_12_meshResampling(binPath,baseDir , simplificationFactor=0.8 , maxVertices=15000):
#     taskFolder = "/12_MeshResampling"
#     SilentMkdir(baseDir + taskFolder)

#     print("----------------------- 12/13 MESH RESAMPLING -----------------------")
#     inputMesh = "\"" + baseDir +  "/11_MeshDecimate/mesh.obj" + "\""
#     outputMesh = "\"" + baseDir  + taskFolder + "/mesh.obj" + "\""

#     cmdLine = binPath + "\\aliceVision_meshResampling.exe"
#     cmdLine += " --input {0}  --output {1}".format( inputMesh, outputMesh)

#     cmdLine += " --verboseLevel " + verboseLevel
#     cmdLine += " --simplificationFactor " + str(simplificationFactor)
#     cmdLine += " --maxVertices " + str(maxVertices)

#     print(cmdLine)
#     os.system(cmdLine)


def run_13_texturing(binPath , baseDir , textureSide = 4096 , downscale=4 , unwrapMethod = "Basic"):
    taskFolder = "/13_Texturing"
    SilentMkdir(baseDir + taskFolder)

    print("----------------------- 13/13 TEXTURING  -----------------------")
    _input = "\"" + baseDir +   "/9_Meshing/densePointCloud.abc" + "\""
    imagesFolder = "\""  + baseDir + "/6_PrepareDenseScene" "\""
    inputMesh = "\"" + baseDir + "/10_MeshFiltering/mesh.obj" + "\""
    output = "\"" + baseDir + taskFolder + "\""

    cmdLine = binPath + "\\aliceVision_texturing.exe"
    cmdLine += " --input {0} --inputMesh {1} --output {2} --imagesFolder {3}".format(
        _input, inputMesh, output, imagesFolder)

    cmdLine += " --textureSide " + str(textureSide)
    cmdLine += " --downscale " + str(downscale)
    cmdLine += " --verboseLevel " + verboseLevel
    #cmdLine += " --unwrapMethod " + unwrapMethod
    cmdLine += " --outputTextureFileType png --unwrapMethod Basic --useUDIM True --fillHoles False --padding 5 --multiBandDownscale 4 --multiBandNbContrib 1 5 10 0 --useScore True --bestScoreThreshold 0.1 --angleHardThreshold 90.0 --processColorspace sRGB --correctEV False --forceVisibleByAllVertices False --flipNormals False --visibilityRemappingMethod PullPush --subdivisionTargetRatio 0.8"

    print(cmdLine)
    os.system(cmdLine)



def main():
    

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
    # run_11_meshDecimate(binPath,baseDir)
    # run_12_meshResampling(binPath,baseDir)
    run_13_texturing(binPath,baseDir)

    
    print("-------------------------------- DONE ----------------------")
    endTime = time.time()
    hours, rem = divmod(endTime-startTime, 3600)
    minutes, seconds = divmod(rem, 60)
    print("time elapsed: "+"{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds))
    print("press any key to close")


