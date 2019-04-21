#BSD 3-Clause License
#=======
#
#Copyright (c) 2017, Xilinx
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:
#
#* Redistributions of source code must retain the above copyright notice, this
#  list of conditions and the following disclaimer.
#
#* Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation
#  and/or other materials provided with the distribution.
#
#* Neither the name of the copyright holder nor the names of its
#  contributors may be used to endorse or promote products derived from
#  this software without specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
#FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import sys
from finnthesizer import *

if __name__ == "__main__":

    bnnRoot = "."
    npzFile = bnnRoot + "/weights/cifar100-w1a1.npz"
    targetDirBin = bnnRoot + "/binparam-cnvW1A1-pynq"
    targetDirHLS = bnnRoot + "/binparam-cnvW1A1-pynq/hw"
    
    num_classes = 100
    conv_layers = 6
    fc_layers = 3

    #topology of convolutional layers (only for config.h defines)
    ifm       = [32, 30,  14,  12,   5,   3]
    ofm       = [30, 28,  12,  10,   3,   1]   
    ifm_ch    = [ 3, 64,  64, 128, 128, 256]
    ofm_ch    = [64, 64, 128, 128, 256, 256]   
    filterDim = [ 3,  3,   3,   3,   3,   3]

    WeightsPrecisions_fractional =    [0 , 0 , 0 , 0 , 0 , 0 , 0, 0,  0]
    ActivationPrecisions_fractional = [0 , 0 , 0 , 0 , 0 , 0 , 0, 0,  0]
    InputPrecisions_fractional =      [7 , 0 , 0 , 0 , 0 , 0 , 0, 0,  0]
    WeightsPrecisions_integer =       [1 , 1 , 1 , 1 , 1 , 1 , 1, 1,  1]
    ActivationPrecisions_integer =    [1 , 1 , 1 , 1 , 1 , 1 , 1, 1, 16]
    InputPrecisions_integer =         [1 , 1 , 1 , 1 , 1 , 1 , 1, 1,  1]
    if num_classes == 10:
    	classes = ['Airplane', 'Automobile', 'Bird', 'Cat', 'Deer', 'Dog', 'Frog', 'Horse', 'Ship', 'Truck']
    elif num_classes == 100:
    	classes = ['beaver', 'dolphin', 'otter', 'seal', 'whale', 'aquarium fish', 'flatfish', 'ray', 'shark', 'trout',
    		   'orchids', 'poppies', 'roses', 'sunflowers', 'tulips', 'bottles', 'bowls', 'cans', 'cups', 'plates',
    		   'apples', 'mushrooms', 'oranges', 'pears', 'sweet peppers', 'clock', 'computer keyboard', 'lamp', 'telephone', 'television',
    		   'bed', 'chair', 'couch', 'table', 'wardrobe', 'bee', 'beetle', 'butterfly', 'caterpillar', 'cockroach', 
    		   'bear', 'leopard', 'lion', 'tiger', 'wolf', 'bridge', 'castle', 'house', 'road', 'skyscraper',
    		   'cloud', 'forest', 'mountain', 'plain', 'sea', 'camel', 'cattle', 'chimpanzee', 'elephant', 'kangaroo',
    		   'fox', 'porcupine', 'possum', 'raccoon', 'skunk', 'crab', 'lobster', 'snail', 'spider', 'worm',
    		   'baby', 'boy', 'girl', 'man', 'woman', 'crocodile', 'dinosaur', 'lizard', 'snake', 'turtle',
    		   'hamster', 'mouse', 'rabbit', 'shrew', 'squirrel', 'maple', 'oak', 'palm', 'pine', 'willow',
    		   'bicycle', 'bus', 'motorcycle', 'pickup truck', 'train', 'lawn-mower', 'rocket', 'streetcar', 'tank', 'tractor']

    #configuration of PE and SIMD counts
    peCounts =    [16, 32, 16, 16,  4,  1, 1, 1, 4]
    simdCounts =  [ 3, 32, 32, 32, 32, 32, 4, 8, 1]


    if not os.path.exists(targetDirBin):
      os.mkdir(targetDirBin)
    if not os.path.exists(targetDirHLS):
      os.mkdir(targetDirHLS)    

    #read weights
    rHW = BNNWeightReader(npzFile, True)

    config = "/**\n"
    config+= " * Finnthesizer Config-File Generation\n";
    config+= " *\n **/\n\n"
    config+= "#ifndef __LAYER_CONFIG_H_\n#define __LAYER_CONFIG_H_\n\n"

    # process convolutional layers
    for convl in range(0, conv_layers):
      peCount = peCounts[convl]
      simdCount = simdCounts[convl]
      WPrecision_fractional = WeightsPrecisions_fractional[convl]
      APrecision_fractional = ActivationPrecisions_fractional[convl]
      IPrecision_fractional = InputPrecisions_fractional[convl]
      WPrecision_integer = WeightsPrecisions_integer[convl]
      APrecision_integer = ActivationPrecisions_integer[convl]
      IPrecision_integer = InputPrecisions_integer[convl]
      print("Using peCount = %d simdCount = %d for engine %d" % (peCount, simdCount, convl))
      if convl == 0:
        # use fixed point weights for the first layer
        (w,t) = rHW.readConvBNComplex(WPrecision_fractional, APrecision_fractional, IPrecision_fractional, WPrecision_integer, APrecision_integer, IPrecision_integer, usePopCount=False)
        # compute the padded width and height
        paddedH = padTo(w.shape[0], peCount)
        paddedW = padTo(w.shape[1], simdCount)
        # compute memory needed for weights and thresholds
        neededWMem = (paddedW * paddedH) // (simdCount * peCount)
        neededTMem = paddedH // peCount
        print("Layer %d: %d x %d" % (convl, paddedH, paddedW))
        print("WMem = %d TMem = %d" % (neededWMem, neededTMem))
        print("IPrecision = %d.%d WPrecision = %d.%d APrecision = %d.%d" % (IPrecision_integer, IPrecision_fractional, WPrecision_integer,WPrecision_fractional, APrecision_integer, APrecision_fractional))

        m = BNNProcElemMem(peCount, simdCount, neededWMem, neededTMem, WPrecision_integer, APrecision_integer, IPrecision_integer, WPrecision_fractional, APrecision_fractional, IPrecision_fractional, numThresBits=24, numThresIntBits=16)
        m.addMatrix(w,t,paddedW,paddedH)


        config += (printConvDefines("L%d" % convl, filterDim[convl], ifm_ch[convl], ifm[convl], ofm_ch[convl], ofm[convl], simdCount, peCount, neededWMem, neededTMem, WPrecision_integer, APrecision_integer, WPrecision_fractional, APrecision_fractional)) + "\n" 

        #generate HLS weight and threshold header file to initialize memory directly on bitstream generation       
        #m.createHLSInitFiles(targetDirHLS + "/memdata-" + str(convl) + ".h", str(convl))

        #generate binary weight and threshold files to initialize memory during runtime
        #because HLS might not work for very large header files        
        m.createBinFiles(targetDirBin, str(convl))

      else:
        # regular binarized layer
        (w,t) = rHW.readConvBNComplex(WPrecision_fractional, APrecision_fractional, IPrecision_fractional, WPrecision_integer, APrecision_integer, IPrecision_integer)
        # compute the padded width and height
        paddedH = padTo(w.shape[0], peCount)
        paddedW = padTo(w.shape[1], simdCount)
        # compute memory needed for weights and thresholds
        neededWMem = (paddedW * paddedH) // (simdCount * peCount)
        neededTMem = paddedH // peCount
        print("Layer %d: %d x %d" % (convl, paddedH, paddedW))
        print("WMem = %d TMem = %d" % (neededWMem, neededTMem))
        print("IPrecision = %d.%d WPrecision = %d.%d APrecision = %d.%d" % (IPrecision_integer, IPrecision_fractional, WPrecision_integer,WPrecision_fractional, APrecision_integer, APrecision_fractional))
        m = BNNProcElemMem(peCount, simdCount, neededWMem, neededTMem, WPrecision_integer, APrecision_integer, IPrecision_integer, WPrecision_fractional, APrecision_fractional, IPrecision_fractional)
        m.addMatrix(w,t,paddedW,paddedH)

        config += (printConvDefines("L%d" % convl, filterDim[convl], ifm_ch[convl], ifm[convl], ofm_ch[convl], ofm[convl], simdCount, peCount, neededWMem, neededTMem, WPrecision_integer, APrecision_integer, WPrecision_fractional, APrecision_fractional)) + "\n" 

        #generate HLS weight and threshold header file to initialize memory directly on bitstream generation        
        #m.createHLSInitFiles(targetDirHLS + "/memdata-" + str(convl) + ".h", str(convl))

        #generate binary weight and threshold files to initialize memory during runtime
        #because HLS might not work for very large header files        
        m.createBinFiles(targetDirBin, str(convl))

    # process fully-connected layers
    for fcl in range(conv_layers,conv_layers + fc_layers):
      peCount = peCounts[fcl]
      simdCount = simdCounts[fcl]
      WPrecision_fractional = WeightsPrecisions_fractional[fcl]
      APrecision_fractional = ActivationPrecisions_fractional[fcl]
      IPrecision_fractional = InputPrecisions_fractional[fcl]
      WPrecision_integer = WeightsPrecisions_integer[fcl]
      APrecision_integer = ActivationPrecisions_integer[fcl]
      IPrecision_integer = InputPrecisions_integer[fcl]
      print("Using peCount = %d simdCount = %d for engine %d" % (peCount, simdCount, fcl))
      (w,t) =  rHW.readFCBNComplex(WPrecision_fractional, APrecision_fractional, IPrecision_fractional, WPrecision_integer, APrecision_integer, IPrecision_integer)
      # compute the padded width and height
      paddedH = padTo(w.shape[0], peCount)
      if (fcl == conv_layers + fc_layers - 1):
        paddedH = padTo(w.shape[0], 64)
      paddedW = padTo(w.shape[1], simdCount)
      # compute memory needed for weights and thresholds
      neededWMem = (paddedW * paddedH) // (simdCount * peCount)
      neededTMem = paddedH // peCount
      print("Layer %d: %d x %d" % (fcl, paddedH, paddedW))
      print("WMem = %d TMem = %d" % (neededWMem, neededTMem))
      print("IPrecision = %d.%d WPrecision = %d.%d APrecision = %d.%d" % (IPrecision_integer, IPrecision_fractional, WPrecision_integer,WPrecision_fractional, APrecision_integer, APrecision_fractional))

      m = BNNProcElemMem(peCount, simdCount, neededWMem, neededTMem, WPrecision_integer, APrecision_integer, IPrecision_integer, WPrecision_fractional, APrecision_fractional, IPrecision_fractional)
      m.addMatrix(w,t,paddedW,paddedH)

      config += (printFCDefines("L%d" % fcl, simdCount, peCount, neededWMem, neededTMem, paddedW, paddedH, WPrecision_integer, APrecision_integer, WPrecision_fractional, APrecision_fractional)) + "\n" 

      #generate HLS weight and threshold header file to initialize memory directly on bitstream generation
      #if (fcl == conv_layers + fc_layers - 1):
      # m.createHLSInitFiles(targetDirHLS + "/memdata-" + str(fcl) + ".h", str(fcl), writethreshs = False)
      #else:
      # m.createHLSInitFiles(targetDirHLS + "/memdata-" + str(fcl) + ".h", str(fcl))

      #generate binary weight and threshold files to initialize memory during runtime
      #because HLS might not work for very large header files        
      m.createBinFiles(targetDirBin, str(fcl))

    config+="\n#define LL_MH %d" %paddedH
    config+="\n#define IMG_DIM %d" %ifm[0]
    config+="\n#define IMG_CH %d" %ifm_ch[0]
    config+="\n#define no_cl %d" %w.shape[0]
    config+="\n\n#endif //__LAYER_CONFIG_H_\n\n"


    configFile = open(targetDirHLS+"/config.h", "w")
    configFile.write(config)
    configFile.close()

    with open(targetDirBin + "/classes.txt", "w") as f:
        f.write("\n".join(classes))

