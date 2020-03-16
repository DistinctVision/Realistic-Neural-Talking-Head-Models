"""Main"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from datetime import datetime
import matplotlib
#matplotlib.use('agg')
from matplotlib import pyplot as plt
plt.ion()
import os

from dataset.dataset_class import PreprocessDataset
from dataset.video_extraction_conversion import *
from loss.loss_discriminator import *
from loss.loss_generator import *
from network.blocks import *
from network.model import *
from tqdm import tqdm

from params.params import K, path_to_chkpt, path_to_backup, path_to_Wi, batch_size, path_to_preprocess, frame_shape

"""Create dataset and net"""
display_training = True
device = torch.device("cuda:0")
cpu = torch.device("cpu")
dataset = PreprocessDataset(K=K, path_to_preprocess=path_to_preprocess, path_to_Wi=path_to_Wi)
dataLoader = DataLoader(dataset, batch_size=2, shuffle=True, num_workers=16, pin_memory=True)

E = Embedder(frame_shape).to(device)
D = Discriminator(dataset.__len__(), path_to_Wi)

E.train()

"""Training init"""
epochCurrent = epoch = i_batch = 0
lossesG = []
lossesD = []
i_batch_current = 0

num_epochs = 1

#initiate checkpoint if inexistant
if not os.path.isfile(path_to_chkpt):
  print('Initiating new checkpoint...')
  torch.save({
          'epoch': epoch,
          'lossesG': lossesG,
          'lossesD': lossesD,
          'E_state_dict': E.state_dict(),
          'G_state_dict': G.state_dict(),
          'D_state_dict': D.state_dict(),
          'num_vid': dataset.__len__(),
          'i_batch': i_batch
          }, path_to_chkpt)
  print('...Done')

"""Loading from past checkpoint"""
checkpoint = torch.load(path_to_chkpt, map_location=cpu)
E.load_state_dict(checkpoint['E_state_dict'])
num_vid = checkpoint['num_vid']

E.train()


"""Training"""
batch_start = datetime.now()
pbar = tqdm(dataLoader, leave=True, initial=i_batch_current)
if not display_training:
    matplotlib.use('agg')

with torch.no_grad():
    for epoch in range(epochCurrent, num_epochs):
        if epoch > epochCurrent:
            i_batch_current = 0
            pbar = tqdm(dataLoader, leave=True, initial=i_batch_current)
        pbar.set_postfix(epoch=epoch)
        for i_batch, (f_lm, x, g_y, i, W_i) in enumerate(pbar, start=i_batch_current):
            
            f_lm = f_lm.to(device)
            
            with torch.autograd.enable_grad():
                #zero the parameter gradients
                
                #forward
                # Calculate average encoding vector for video
                f_lm_compact = f_lm.view(-1, f_lm.shape[-4], f_lm.shape[-3], f_lm.shape[-2], f_lm.shape[-1]) #BxK,2,3,224,224
                
                e_vectors = E(f_lm_compact[:,0,:,:,:], f_lm_compact[:,1,:,:,:]) #BxK,512,1
                e_vectors = e_vectors.view(-1, f_lm.shape[1], 512, 1) #B,K,512,1
                e_hat = e_vectors.mean(dim=1)
    
    
            for enum, idx in enumerate(i):
                torch.save({'W_i': e_hat[enum,:].unsqueeze(0)}, path_to_Wi+'/W_'+str(idx.item())+'/W_'+str(idx.item())+'.tar')
                        
