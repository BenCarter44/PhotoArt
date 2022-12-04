import cv2
import tqdm
import numpy as np
import json
import pickle
import os


IS_FLIPPED = False
STYLE_PARTS = 5
SKIP = True

fn = open("selection.txt")

FILENAME = "photos/" + fn.read().rstrip()
fn.close()

def mapValue(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def binSearch(lst,locatedVal):
  #  print(lst)
    if(len(lst) == 1):
        return lst[0]
    if(lst[len(lst) // 2] > locatedVal):
        return binSearch(lst[0:len(lst) // 2],locatedVal)
    else:
        return binSearch(lst[len(lst) // 2:],locatedVal)
        
    pass


# one character is 4:1.8   height:width.

def cropCenter(starter,newHeight,newWidth):
    startDim = starter.shape[:2]
    offsetHeight = (startDim[0] - newHeight) // 2
    offsetWidth = (startDim[1] - newWidth) // 2
    

    return starter[offsetHeight:newHeight+offsetHeight, offsetWidth:newWidth+offsetWidth,:]


def segments(im,blockY,blockX,blockHeight,blockWidth):
    return im[blockY*blockHeight:blockY*blockHeight+blockHeight,blockX*blockWidth:blockX*blockWidth+blockWidth,:]


def prepareImage(starter,setHeight,setWidth): # [height,width,depth]
    out = []
    theDim = starter.shape[:2]

    if(theDim[1] < setWidth): # image is too small, SO GROW IT.
        scaler = theDim[0] / theDim[1]
        starter = cv2.resize(starter,(int(setWidth),int(setWidth * scaler)),cv2.INTER_CUBIC)
        theDim = starter.shape[:2]
    

    pixelsPerWidthBlock = theDim[1] / setWidth
    pixelsPerHeightBlock = pixelsPerWidthBlock * 21 / 9

    blocksWide = int(theDim[1] / pixelsPerWidthBlock)
    blocksTall = int(theDim[0] / pixelsPerHeightBlock)


    if(blocksTall > setHeight):
        # the picture won't fit! Scale down!
        if(theDim[0] < setHeight): # image is too small!
            scaler = theDim[1] / theDim[0]
            starter = cv2.resize(starter,(int(setHeight * scaler),int(setHeight)),cv2.INTER_CUBIC)
            theDim = starter.shape[:2]

        pixelsPerHeightBlock = theDim[0] / setHeight 
        pixelsPerWidthBlock = pixelsPerHeightBlock * 9 / 21
        
        blocksWide = int(theDim[1] / pixelsPerWidthBlock)
        blocksTall = int(theDim[0] / pixelsPerHeightBlock)



    pixelsPerWidthBlock = int(pixelsPerWidthBlock)
    pixelsPerHeightBlock = int(pixelsPerHeightBlock)
    
    newDim = [blocksTall * pixelsPerHeightBlock,blocksWide * pixelsPerWidthBlock]
  #  print(theDim)
  #  print(pixelsPerHeightBlock,pixelsPerWidthBlock)
  #  print(blocksTall,blocksWide)
    niceStarter = cropCenter(starter,newDim[0],newDim[1])
    #cv2.imshow("niceCrop",niceStarter)
    #cv2.waitKey()
    cv2.destroyAllWindows()
    out = {"maxBlocksW":blocksWide,"maxBlocksH":blocksTall,"pixW":pixelsPerWidthBlock,"pixH":pixelsPerHeightBlock,"blockData":{}}
    print("Separating photos")
    bargraph = tqdm.tqdm(total=blocksTall*blocksWide)
    for y in range(blocksTall):
        for x in range(blocksWide): 
            ou = segments(niceStarter,y,x,pixelsPerHeightBlock,pixelsPerWidthBlock)
            pTokens = ou.shape[:2]
          #  print(pTokens)
            pTokens = [pTokens[1] * 5,pTokens[0] * 5]
          #  print(pTokens)
          #  print(tuple(pTokens))
          #  preview = cv2.resize(ou,dsize=tuple(pTokens),interpolation=cv2.INTER_AREA) # but dsize for resize is width by height!
          #  print(preview.shape)
            averageColorR = np.average(ou,axis=0)
            averageColor = np.average(averageColorR,axis=0)
            d_img = np.ones((75*5,32 *5,3), dtype=np.uint8)
            d_img[:,:] = averageColor
          #  cv2.imshow("raw",preview)
         #   print(averageColor)
            out["blockData"]["r%sc%s"%(y,x)] = list(averageColor)
            bargraph.update(1)
           # cv2.imshow(str(averageColor),d_img)
           # cv2.waitKey()
           # cv2.destroyAllWindows()
            
    return out   
    
   # smallImg = cv2.resize(starter,(height,width),cv2.INTER_AREA)


def colorMatch(color,colormap):
    # OPENCV is flipped! BGR

    txtparts = colormap["cm"]
    weights = colormap["w"]
    gray = color[2] * 0.299 + color[1] * 0.587 + color[0] * 0.114

   # HLS = cv2.COLOR_BGR2HLS(color) # h is now 


    averageBlue = color[0]
    averageGreen = color[1]
    averageRed = color[2]

    sectionSize = 255 / STYLE_PARTS


    blueBlock = averageBlue / sectionSize # in sections of 51. (255 / style)
    greenBlock = averageGreen / sectionSize
    redBlock = averageRed / sectionSize

    lowBlue = int(blueBlock) * sectionSize
    highBlue = int(blueBlock + 1) * sectionSize
    lowGreen = int(greenBlock)* sectionSize
    highGreen = int(greenBlock + 1) * sectionSize
    lowRed = int(redBlock) * sectionSize
    highRed = int(redBlock + 1) * sectionSize

    if(highBlue > 255):
        highBlue = 255
    if(highGreen > 255):
        highGreen = 255
    if(highRed > 255):
        highRed = 255
    
    matrix = [
        [lowBlue,lowGreen,lowRed],
        [lowBlue,highGreen,lowRed],
        [lowBlue,lowGreen,highRed],
        [lowBlue,highGreen,highRed],
        [highBlue,lowGreen,lowRed],
        [highBlue,highGreen,lowRed],
        [highBlue,lowGreen,highRed],
        [highBlue,highGreen,highRed]
    ]
    grayValLow = 1000
    grayValHigh = -1000
    for x in matrix:
        i = x[2] * 0.299 + x[1] * 0.587 + x[0] * 0.114
        if(i < grayValLow):
            grayValLow = i
        if(i > grayValHigh):
            grayValHigh = i
    
    
    boundedLow = [lowRed,lowGreen,lowBlue]
    boundedHigh = [highRed,highGreen,highBlue]

    backOut = boundedHigh
    textColorOut = boundedHigh
    fun = 0
    if(grayValHigh != grayValLow):
        # closer to low.
        backOut = boundedLow
        textColorOut = boundedHigh

        adjustedValue = binSearch(weights,(gray - grayValLow) / (grayValHigh - grayValLow))
        fun = (gray - grayValLow) / (grayValHigh - grayValLow)
        txtNum = weights.index(adjustedValue)
        
    else:
        txtNum = 0
        backOut = boundedHigh
        textColorOut = boundedHigh
#
  #  else:
 #       backOut = boundedHigh
 ##       txtColorOut = boundedLow
 #       adjustedValue = binSearch(weights,(grayValHigh - gray) / ((grayValHigh - grayValLow) / 2))
 #       fun = (grayValHigh - gray) / ((grayValHigh - grayValLow) / 2)
 #       txtNum = weights.index(adjustedValue)
   # print(backOut,gray,grayValLow)
    return [txtNum,textColorOut,backOut] #,fun,grayValHigh,grayValLow,gray]





col,row = os.get_terminal_size()
print(row)
print(col)

try:
    f = open(FILENAME + ".json")
    json.load(f)
    f.close()
except:
    SKIP = False

if(not(SKIP)):

    fileMoon = cv2.imread(FILENAME)
    #cv2.imshow("original",fileMoon)
    #cv2.waitKey()
    #cv2.destroyAllWindows()
    out = prepareImage(fileMoon,row,col)
    f = open(FILENAME + ".json",'w')
    json.dump(out,f)
    f.close()
else:
    f = open(FILENAME + ".json")
    out = json.load(f)
    f.close()


f = open("colorMapping.dat",'rb')
colormap = pickle.load(f)
f.close()

width = out["maxBlocksW"]
height = out["maxBlocksH"]
if(height > row):
    print("TooSmall!")
if(not(width == col or height == row)):
    print("Size changed!")
    fileMoon = cv2.imread(FILENAME)
    #cv2.imshow("original",fileMoon)
    #cv2.waitKey()
    #cv2.destroyAllWindows()
    out = prepareImage(fileMoon,row,col)
    f = open(FILENAME + ".json",'w')
    json.dump(out,f)
    f.close()
    width = out["maxBlocksW"]
    height = out["maxBlocksH"]


#for x in range(256):
#    outT = colorMatch([x,x,x],colormap)
#    print(x,outT)


#input()

dat = out["blockData"]
dump = ""

f = open("transferCOLOR.toc",'w')
f.write(str(width))
f.write(" ")
f.write(str(height))
f.write(" ")
#debug = ""
print("Rendering colors")
pbar = tqdm.tqdm(total=height*width)
for y in range(height):
    for x in range(width):
        out = colorMatch(dat["r%sc%s"%(y,x)],colormap)
     #   debug += str(out[0]) + "," + str(out[1]) + " "
        txtColor = out[1]
        backColor = out[2]

        dump = str(int(out[0])) + " " + str(int(txtColor[0])) + " " + str(int(txtColor[1])) + " " + str(int(txtColor[2])) + " " + str(int(backColor[0])) + " " + str(int(backColor[1])) + " " + str(int(backColor[2])) + " "
        f.write(dump)
        pbar.update(1)
    dump = ""
    #print(debug)
   # debug = ""
f.close()






