# SDAC-DA
Semi-supervised Deep Attributed Clustering using Dual Autoencoder
 Run the code using the following steps:
1.  upload the code in Google Colab .
2. Copy the content of dataset folder to your google drive.
3. For detecting name of dataset file in the source code it is enough to store dataset name in line 4 in variable dname.
4. For detecting number of cluster it is enough to store it in variable num_c  in line 2.
To run the code on other dataset  consider the following notice:
***To run the code on each dataset , we should have three fie:
1. Adjacency file:   is a .dat file that each line of this file contain two number (id of nodes in each edge)separated by tab . For example cora.dat
2. Feature file: is a .dat file that i’th line of this file contains numbers separated by space detecting attributes of i’th node. For example cora_f.dat
3. ground truth file: : is a .dat file that i’th line of this file contains id of nodes that belong to i’th cluster. For example cora_one.dat

***Notice that the format of file’s name be as following:
1. dataset.dat : Adjacency file
2. dataset_f.dat: Feature file
3. dataset_one.dat: ground truth file
If you have any question you can send it through Kamal.berahmand@hdr.qut.edu.au. 


