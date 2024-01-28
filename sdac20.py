# -*- coding: utf-8 -*-
"""SDAC20.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/14cY1Dm9jbY2H6KgFEG7QRvbmw6Sb1x3g
"""

#detect number of communities
num_c=2
#detect name of dataset
dname='cora'

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import euclidean_distances
import tensorflow as tf
from sklearn.cluster import KMeans
import random


# define the manifold autoencoder for the adjacency matrix
def adjacency_autoencoder(input_dim, latent_dim):
    encoder = tf.keras.models.Sequential([
        tf.keras.layers.InputLayer(input_shape=(input_dim,)),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(latent_dim, activation=None),
    ])

    decoder = tf.keras.models.Sequential([
        tf.keras.layers.InputLayer(input_shape=(latent_dim,)),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(input_dim, activation=None),
    ])

    return encoder, decoder

# define the manifold autoencoder for the attribute matrix
def attribute_autoencoder(input_dim, latent_dim):
    encoder = tf.keras.models.Sequential([
        tf.keras.layers.InputLayer(input_shape=(input_dim,)),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(latent_dim, activation=None),
    ])

    decoder = tf.keras.models.Sequential([
       tf.keras.layers.InputLayer(input_shape=(latent_dim,)),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(input_dim, activation=None),
    ])

    return encoder, decoder
def create_Cs_matrix(D, S, adjacency_matrix):
  num_nodes =D.shape[0]
  Cs=np.zeros((num_nodes, num_nodes))
  for i in range(num_nodes):
       for j in range(num_nodes):
          if D[i,j]<S[i] and adjacency_matrix[i,j]==0 :
              Cs[i,j]=1
          if D[i,j]>S[i] and adjacency_matrix[i,j]==0 :
              Cs[i,j]=-1

  return Cs
def create_Ct_matrix(D1, S1, adjacency_matrix):
    num_nodes =D1.shape[0]
    Ct=np.zeros((num_nodes, num_nodes))
    for i in range(num_nodes):
       for j in range(num_nodes):
          if D1[i,j]<S1[i] and adjacency_matrix[i,j]==0 :
              Ct[i,j]=1
          if D1[i,j]>S1[i] and adjacency_matrix[i,j]==0 :
              Ct[i,j]=-1
    return Ct
def calculate_distance_matrix(matrix):
    return np.linalg.norm(matrix[:, np.newaxis] - matrix, axis=2)
# define the optimizer and loss function
def optimizer(repeats, adjacency_encoder, attribute_encoder, Ct, Cs):
    def loss_function(A, M):
        def adjacency_loss(A, A_hat, Z, Cs):
           L_A = np.linalg.norm(A -A_hat)
           L_Z = 0
           for i in range(len(Z)):
              for j in range(len(Z)):
               L_Z +=np.linalg.norm(Z[i] - Z[j], ord=1) * Cs[i][j]
           l1=L_A + L_Z
           return l1
        def attribute_loss(M, M_hat, Z, Ct):


           L_M = np.linalg.norm(M - M_hat)
           L_Z = 0
           for i in range(M.shape[0]):
              for j in range(M.shape[0]):
                   L_Z += np.linalg.norm(Z[i] - Z[j]) * Ct[i][j]
           l1=L_M + L_Z
           return l1
        # calculate the latent representations for A and M
        z_A = adjacency_encoder(A)
        z_M = attribute_encoder(M)

        # calculate the reconstruction loss for A and M
        A_hat = adjacency_decoder(z_A)
        M_hat = attribute_decoder(z_M)
        Z1 = tf.zeros((A.shape[0], latent_dim))
        Z2=tf.zeros((M.shape[0], latent_dim))
        reconstruction_loss =adjacency_loss(A, A_hat, Z1, Cs)+attribute_loss(M, M_hat, Z2, Ct) #tf.norm(A - A_hat, ord='euclidean') + tf.norm(M - M_hat, ord='euclidean')

        # calculate the regularization loss
        regularizer_loss = 0

        # calculate the clustering loss and update the cluster assignments
        Z = tf.zeros((A.shape[0], latent_dim))
        Z_prev = tf.zeros((A.shape[0], latent_dim))
        for i in range(repeats):
            # calculate the reconstruction loss for the repeated decoder output
            A_hat= adjacency_decoder(Z)
            M_hat = attribute_decoder(Z)
            Z1 = tf.zeros((A.shape[0], latent_dim))
            Z2=tf.zeros((M.shape[0], latent_dim))
            #reconstruction_loss +=attribute_loss(M, M_hat, Z2, Ct)
            reconstruction_loss +=adjacency_loss(A, A_hat, Z1, Cs)+attribute_loss(M, M_hat, Z2, Ct)# tf.norm(A - Av, ord='euclidean') + tf.norm(M - Mv, ord='euclidean')
            # Calculate Frobenius norm of Zs and Zt
            Zs=adjacency_encoder(A_hat)
            Zt=attribute_encoder(M_hat)
            frobenius_norm =0# np.linalg.norm(Zs - Zt, ord='fro')

            # update the clustering assignments

            Z_prev = Z
            Z = adjacency_encoder(A_hat) + attribute_encoder(M_hat)
            cluster_loss = tf.keras.losses.kl_divergence(Z_prev, Z)
            cluster_loss += tf.keras.losses.kl_divergence(Z, Z_prev)
            cluster_loss /= 2

            K = num_c

            # Perform K-means clustering
            kmeans = KMeans(n_clusters=K, init='k-means++')
            cluster_labels = kmeans.fit_predict(Z)

            # Compute the soft label probabilities
            cluster_centers = kmeans.cluster_centers_
            p_ij = np.exp(-euclidean_distances(Z, cluster_centers) ** 2)

            # Compute the value of q_ij
            q_ij = (p_ij ** 2) / np.sum(p_ij, axis=0)
            q_ij /= np.sum(q_ij, axis=1, keepdims=True)

            # Compute the KL-divergence loss
            kl_loss = np.sum(q_ij * np.log(q_ij / p_ij))

        # return the total loss
        return reconstruction_loss+ cluster_loss+ frobenius_norm + kl_loss

    return loss_function

import numpy as np
from google.colab import drive
drive.mount('/content/drive')
file_path = '/content/drive/My Drive/'+dname+'.dat'
# Read the file and create the matrix
with open(file_path, 'r') as file:
    lines = file.readlines()
max_m = 0
max_n = 0

for line in lines:
    m, n = map(int, line.split())
    max_m = max(max_m, m)
    max_n = max(max_n, n)
max1=max(max_m , max_n)
matrix_size = (max1 , max1 )
A = np.zeros(matrix_size)
for line in lines:
    m, n = map(int, line.split())
    A[m-1, n-1] = 1
    A[n-1, m-1] = 1

#n=162
#A = np.zeros((n,n))

#with open(file_path, 'r') as file:
#    for line in file:
#        words = line.split()
        #print(line)
 #       i=int(words[0])
 #       i-=1
  #      j=int(words[1])
  #      j-=1
  #      A[i,j]=1

file_path = '/content/drive/My Drive/'+dname+'_f.dat'

# Open the input file and read its contents
with open(file_path, 'r') as f:
    lines = f.readlines()

# Create an empty dictionary to hold the feature values for each node
features = {}

# Iterate over each line in the input file
i=0
for line in lines:
    # Split the line into node index and feature values
    parts = line.split()
    node_index = int(parts[0])
    node_index-=1
    feature_values =[int(x) for x in parts[1:]]# [int(x) for x in parts[0:]]

    # Add the feature values to the dictionary for this node
    features[i] = feature_values
    i+=1

# Determine the number of nodes and the number of features per node
num_nodes = len(features)
num_features =len(features[0])

print(num_nodes)
print(num_features)
# Create an empty matrix to hold the feature values for all nodes
F = np.zeros((num_nodes, num_features))

# Fill in the feature matrix
for i in range(n):
    F[i, :] = features[i]
M=np.zeros_like(F)
M = F / np.sum(F, axis=1, keepdims=True)

# Euclidean distance matrix
n = F.shape[0]
D = calculate_distance_matrix(A)
S1 = np.mean(D, axis=1)
Cs = create_Cs_matrix(D, S1, A)

# Convert attribute matrix to Markov matrix and calculate Euclidean distances and create Ct matrix

D1 = np.zeros_like(A)
num_nodes=F.shape[0]
num_features=F.shape[1]
for i in range(num_nodes):
    for j in range(i+1, num_nodes):
        d = np.sqrt(np.sum((F[i] - F[j])**2))
        D[i, j] = d
        D[j, i] = d
S2 = np.mean(D, axis=1)
#print(S2[1,])
Ct = create_Ct_matrix(D1, S2, A)

# define the hyperparameters
input_dim_A = A.shape[1]
input_dim_M = M.shape[1]
latent_dim = 10
repeats = 5

# create the autoencoder models
adjacency_encoder, adjacency_decoder = adjacency_autoencoder(input_dim_A, latent_dim)
attribute_encoder, attribute_decoder = attribute_autoencoder(input_dim_M, latent_dim)

# define the optimizer
opt = tf.keras.optimizers.Adam()

# compile the models
adjacency_encoder.compile(optimizer=opt, loss='mse')
adjacency_decoder.compile(optimizer=opt, loss='mse')
attribute_encoder.compile(optimizer=opt, loss='mse')
attribute_decoder.compile(optimizer=opt, loss='mse')

# define the loss function
loss_fn = optimizer(repeats, adjacency_encoder, attribute_encoder,Cs , Ct)

# train the models
for i in range(5):
    with tf.GradientTape() as tape:
        loss = loss_fn(A, M)
    gradients = tape.gradient(loss, adjacency_encoder.trainable_variables + attribute_encoder.trainable_variables)
    opt.apply_gradients(zip(gradients, adjacency_encoder.trainable_variables + attribute_encoder.trainable_variables))


# get the final latent representations and cluster assignments
z_A = adjacency_encoder(A)
z_M = attribute_encoder(M)
Z = adjacency_encoder.predict(A) + attribute_encoder.predict(M)
drive.mount('/content/drive')
np.savetxt('/content/drive/My Drive/'+dname+'_two.dat', Z, delimiter=' ')
files.download('/content/drive/My Drive/'+dname+'_two.dat')
Z[np.isnan(Z)] = 0
kmeans = KMeans(num_c).fit(Z)
cluster_assignments = kmeans.labels_
groups = {}
for i, val in enumerate(kmeans.labels_):
    if val not in groups:
        groups[val] = [i+1]
    else:
        groups[val].append(i+1)

# Print the groups
print(groups)
from google.colab import drive
drive.mount('/content/drive')
with open('/content/drive/MyDrive/'+dname+'_two.dat', 'w') as f:
    #Iterate over the dictionary keys and values
    for key, value in groups.items():
        #Convert the list of values to a string
         value_str = ' '.join(str(v) for v in value)
        # Write the key and value to a new line in the file
         f.write(f'{value_str}')
         f.write(f'\n')
from google.colab import files

# Download the file to your local machine
files.download('/content/drive/MyDrive/'+dname+'_two.dat')

from sklearn.metrics.cluster import normalized_mutual_info_score, adjusted_rand_score

# read in the ground truth and predicted labels from the files
from google.colab import drive
drive.mount('/content/drive')
file_path = '/content/drive/My Drive/'+dname+'_one.dat'
with open(file_path, "r") as f:
    ground_truth = [set(line.strip().split()) for line in f.readlines()]
file_path = '/content/drive/My Drive/'+dname+'_two.dat'
with open(file_path, "r") as f:
    predicted_labels = [set(line.strip().split()) for line in f.readlines()]

# convert the label sets to array of integers
j=0
labels_true = []
for i, cluster in enumerate(ground_truth):
    j+=1
    for node in cluster:
        labels_true.append(i)
#print(j)
print(len(labels_true))
j=0
labels_pred = []
for i, cluster in enumerate(predicted_labels):
    j+=1
    for node in cluster:
        labels_pred.append(i)
print(len(labels_pred))
# compute the NMI and ARI
nmi = normalized_mutual_info_score(labels_true, labels_pred)
ari = adjusted_rand_score(labels_true, labels_pred)

print("NMI: {:.3f}".format(nmi))
print("ARI: {:.3f}".format(ari))