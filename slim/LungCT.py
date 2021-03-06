# This Python 3 environment comes with many helpful analytics libraries installed
# It is defined by the kaggle/python docker image: https://github.com/kaggle/docker-python
# For example, here's several helpful packages to load in 

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import skimage, os
from skimage.morphology import ball, disk, dilation, binary_erosion, remove_small_objects, erosion, closing, reconstruction, binary_closing
from skimage.measure import label,regionprops, perimeter
from skimage.morphology import binary_dilation, binary_opening
from skimage.filters import roberts, sobel
from skimage import measure, feature
from skimage.segmentation import clear_border
from skimage import data
from scipy import ndimage as ndi
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import dicom                         # 只能读取单幅 ".dcm"的图像
import scipy.misc
import numpy as np

import SimpleITK as sitk # 医学图像读取 

#--------------------------------------------------------------
# 读取单幅图像
ImgFile = "E:\\Luna16\\subset0\\1.3.6.1.4.1.14519.5.2.1.6279.6001.105756658031515062000744821260.mhd"
inputImg =sitk.ReadImage(ImgFile)

print(inputImg.GetPixelIDTypeAsString()) # 检查图像灰度值的数据类型，判断是否 float类型
Img3D = sitk.Cast(inputImg, sitk.sitkFloat32) # 将图像类型转化为float

print(inputImg.GetHeight(), inputImg.GetWidth(), inputImg.GetDepth()) # 图像shape
print(inputImg.GetDimension()) # 图像维度
sitk.Show(inputImg) # 显示图像

nda = sitk.GetArrayFromImgae(inputImg) # sitk.image 到 np.array
img = sitk.GetImageFromArray(nda)   # 从 np.array到sitk.image

sitk.WriteImage(img, os.path.join(OUTPUT_DIR, 'sitkImg.mha')) # 保存文件
#--------------------------------------------------------------



# read all of 3D CT image with extention '.mhd'
ImgPath = "E:\\Luna16\\subset0"

Img4D = []
for fileName in os.listdir(ImgPath)[0:10]:  # get the first 10 images
    if fileName.endswith(".mhd"):
        Img3D =sitk.ReadImage(os.path.join(ImgPath, fileName))
        Img4D.append(Img3D)
        # = np.stack(Img3D, axis=2) # stack 3D image to 4D image along the 'axie'


# print(Img4D[0]) # 打印 inputImg具有的图像信息，如 size和 spacing
#--------------------------------------------------------------
#       extract the regions of lung 
#--------------------------------------------------------------
def get_segmented_lungs3D(Img3D, threshold=604):
    
    ''' 从 4D images 中逐个取出3D image,然后提取 3D图像中的肺部区域  '''
    
    '''Step 1: 将 3D image 转化为2二值图像'''
    binary = Img3D < threshold 

    '''Step 2: 清楚图像中孤立的图像区域，保证肺部的完整    '''
    cleared = clear_border(binary)

    '''Step 3: Label the image '''
    label_image = label(cleared)

    '''
    Step 4: Keep the labels with 2 largest areas.
    '''
    areas = [r.area for r in regionprops(label_image)]
    areas.sort()
    if len(areas) > 2:
        for region in regionprops(label_image):
            if region.area < areas[-2]:
                for coordinates in region.coords:                
                       label_image[coordinates[0], coordinates[1], coordinates[2]] = 0
    binary = label_image > 0
 
    '''
    Step 5: Erosion operation with a disk of radius 2. This operation is 
    seperate the lung nodules attached to the blood vessels.
    '''
    selem = disk(2)
    binary = binary_erosion(binary, selem)

    '''
    Step 6: Closure operation with a disk of radius 10. This operation is 
    to keep nodules attached to the lung wall.
    '''
    selem = disk(10)
    binary = binary_closing(binary, selem)

    '''
    Step 7: Fill in the small holes inside the binary mask of lungs.
    '''
    edges = roberts(binary)
    binary = ndi.binary_fill_holes(edges)

    '''
    Step 8: Superimpose the binary mask on the input image.
    '''
    get_high_vals = binary == 0
    Img3D[get_high_vals] = 0
        
    return Img3DImg3D
#--------------------------------------------------------------



























# Any results you write to the current directory are saved as output.
lung = dicom.read_file('../input/sample_images/38c4ff5d36b5a6b6dc025435d62a143d.dcm')

slice = lung.pixel_array # 获取 dcm的灰度值矩阵
slice[slice == -2000] = 0
plt.imshow(slice, cmap=plt.cm.gray)


#--------------------------------------------------------------
def read_ct_scan(folder_name):
        # 读取所有的单幅 dcm文件，形成一个 3D体数据
        # slices是一个 list类型
        slices = [dicom.read_file(folder_name + filename) for filename in os.listdir(folder_name)]
        
        # Sort the dicom slices in their respective order
        slices.sort(key=lambda x: int(x.InstanceNumber)) # InstanceNumber是dicom格式自带的一个参数
        
        # Get the pixel values for all the slices
        slices = np.stack([s.pixel_array for s in slices]) #从 3D体数据中逐次读取灰度值矩阵
        slices[slices == -2000] = 0
        return slices
#--------------------------------------------------------------



ct_scan = read_ct_scan('../input/sample_images/') 



def plot_ct_scan(scan):
    # 指定 subplot的行数和列数，figsize的长和宽为25
    # plt.subplots: returns a tuple containing a figure and axes object. 
    # 产生多个子窗口，并以 numpy数组的方式保存在 axes中，可通过对axes进行索引访问每个子窗口。
    # fig是整个图像对象，
    fig, plots = plt.subplots(int(scan.shape[0] / 20) + 1, 4, figsize=(25, 25))
    for i in range(0, scan.shape[0], 5):
        plots[int(i / 20), int((i % 20) / 5)].axis('off')
        plots[int(i / 20), int((i % 20) / 5)].imshow(scan[i], cmap=plt.cm.bone) 

plot_ct_scan(ct_scan)


#-------------------------------------------------------------------

def get_segmented_lungs(im, plot=False):
    
    '''
    This funtion segments the lungs from the given 2D slice.
    '''
    if plot == True:
        f, plots = plt.subplots(8, 1, figsize=(5, 40))

    '''  Step 1: Convert into a binary image.  '''
    # 灰度值阈值化
    binary = im < 604 

    if plot == True:
        plots[0].axis('off')
        plots[0].imshow(binary, cmap=plt.cm.bone) 

    '''Step 2: Remove the blobs connected to the border of the image'''
    # 清除边界之外的 孤立目标
    cleared = clear_border(binary) # clear_border()来自于scikit_image 
    if plot == True:
        plots[1].axis('off')
        plots[1].imshow(cleared, cmap=plt.cm.bone) 

    '''   Step 3: Label the image '''
    # 将所有相邻的标记区域被设置为相同的灰度值
    label_image = label(cleared) # 来自 skimage.measure
    if plot == True:
        plots[2].axis('off')
        plots[2].imshow(label_image, cmap=plt.cm.bone) 

    ''' Step 4: Keep the labels with 2 largest areas '''
    # 计算所有标记区域的面积，注意 [f(i) for i in list] 这种语法
    areas = [r.area for r in regionprops(label_image)] # from skimage.measure
    areas.sort() # 从小到大的顺序排列
    if len(areas) > 2:
        for region in regionprops(label_image):
            if region.area < areas[-2]:
                for coordinates in region.coords:                
                       label_image[coordinates[0], coordinates[1]] = 0

    binary = label_image > 0 # 转化为 True & False
    if plot == True:
        plots[3].axis('off')
        plots[3].imshow(binary, cmap=plt.cm.bone) 
    '''
    Step 5: Erosion operation with a disk of radius 2. This operation is 
    seperate the lung nodules attached to the blood vessels.
    '''
    selem = disk(2)
    binary = binary_erosion(binary, selem)  # from skimage.morphology
    if plot == True:
        plots[4].axis('off')
        plots[4].imshow(binary, cmap=plt.cm.bone) 
    '''
    Step 6: Closure operation with a disk of radius 10. This operation is 
    to keep nodules attached to the lung wall.
    '''
    selem = disk(10)
    binary = binary_closing(binary, selem)
    if plot == True:
        plots[5].axis('off')
        plots[5].imshow(binary, cmap=plt.cm.bone) 
    '''
    Step 7: Fill in the small holes inside the binary mask of lungs.
    '''
    edges = roberts(binary) # roberts边界提取算子
    binary = ndi.binary_fill_holes(edges)
    if plot == True:
        plots[6].axis('off')
        plots[6].imshow(binary, cmap=plt.cm.bone) 
    '''
    Step 8: Superimpose the binary mask on the input image.
    '''
    get_high_vals = binary == 0 # 先计算逻辑判断 (binary==0)，然后赋值
    im[get_high_vals] = 0
    if plot == True:
        plots[7].axis('off')
        plots[7].imshow(im, cmap=plt.cm.bone) 
        
return im
#--------------------------------------------------------------

get_segmented_lungs(ct_scan[71], True)


#--------------------------------------------------------------
def segment_lung_from_ct_scan(ct_scan):
	return np.asarray([get_segmented_lungs(slice) for slice in ct_scan])
#--------------------------------------------------------------    

segmented_ct_scan = segment_lung_from_ct_scan(ct_scan)
plot_ct_scan(segmented_ct_scan)


#--------------------------------------------------------------
def plot_3d(image, threshold=-300):
    
    # Position the scan upright, 
    # so the head of the patient would be at the top facing the camera
    p = image.transpose(2,1,0)
    p = p[:,:,::-1]
    
    verts, faces = measure.marching_cubes(p, threshold)

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Fancy indexing: `verts[faces]` to generate a collection of triangles
    mesh = Poly3DCollection(verts[faces], alpha=0.1)
    face_color = [0.5, 0.5, 1]
    mesh.set_facecolor(face_color)
    ax.add_collection3d(mesh)

    ax.set_xlim(0, p.shape[0])
    ax.set_ylim(0, p.shape[1])
    ax.set_zlim(0, p.shape[2])

    plt.show()
#--------------------------------------------------------------


plot_3d(segmented_ct_scan, 604)


#-------------------------------------------------------------------
# 				2017-04-27
#-------------------------------------------------------------------
segmented_ct_scan = segment_lung_from_ct_scan(ct_scan)
plot_ct_scan(segmented_ct_scan)



#-------------------------------------------------------------------
#对提取的肺部进行灰度值阈值化处理，将灰度值小于604的设置为0
segmented_ct_scan[segmented_ct_scan < 604] = 0
plot_ct_scan(segmented_ct_scan)
#-------------------------------------------------------------------

# 去除肺部的血管信息干扰
selem = ball(2)
binary = binary_closing(segmented_ct_scan, selem)

label_scan = label(binary)

areas = [r.area for r in regionprops(label_scan)]
areas.sort()

for r in regionprops(label_scan):
    max_x, max_y, max_z = 0, 0, 0
    min_x, min_y, min_z = 1000, 1000, 1000
    
    for c in r.coords:
        max_z = max(c[0], max_z)
        max_y = max(c[1], max_y)
        max_x = max(c[2], max_x)
        
        min_z = min(c[0], min_z)
        min_y = min(c[1], min_y)
        min_x = min(c[2], min_x)
    if (min_z == max_z or min_y == max_y or min_x == max_x or r.area > areas[-3]):
        for c in r.coords:
            segmented_ct_scan[c[0], c[1], c[2]] = 0
    else:
        index = (max((max_x - min_x), (max_y - min_y), (max_z - min_z))) / (min((max_x - min_x), (max_y - min_y) , (max_z - min_z)))

#-------------------------------------------------------------------






#-------------------------------------------------------------------        