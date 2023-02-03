# -*- coding: utf-8 -*-
"""vae_minst_torch

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Gqr35_fBfgKiuoXnlhfVL70LwMaNG7RB
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Sep 14 12:16:00 2022

@author: ECURBELO
"""

import torch as t
import torch.nn as nn
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
# from tqdm.notebook import tqdm_notebook as tqdm
from tqdm import tqdm
print('Imported all')

dev = 'cuda' if t.cuda.is_available() else 'cpu'
# dev = 'cpu'
print(dev)

# %% General definitions
input_size = 784 # 28x28
hidden_size = 500 
num_classes = 10
num_epochs = 2
batch_size = 100
learning_rate = 0.001

# %% Get data
train_dataset = torchvision.datasets.MNIST(root='./data',
                                          train=True,
                                          transform=transforms.ToTensor(),
                                          download=True)
test_dataset = torchvision.datasets.MNIST(root='./data',
                                         train=False,
                                         transform=transforms.ToTensor())

# data loader
train_loader = t.utils.data.DataLoader(dataset=train_dataset,
                                      batch_size=batch_size,
                                      shuffle=True)
# %% See data
examples = iter(train_loader)
example_data,example_target = examples.next()
for i in range(6):
    plt.subplot(2,3,i+1)
    plt.imshow(example_data[i][0],cmap='gray')

# %%
class Net(nn.Module):
    
    def __init__(self,input_size,hidden_size,num_classes):
        super(Net,self).__init__()
        self.input_size = input_size
        # self.l1 = nn.Linear(input_size, hidden_size)
        # self.relu = nn.ReLU()
        # self.l2 = nn.Linear(hidden_size, num_classes)
        
        self.encoder = nn.Sequential(
            nn.Linear(input_size,hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size,250),
            nn.ReLU(),
            nn.Linear(250,50),
            nn.ReLU(),
            nn.Linear(50, 2),
            nn.ReLU()
            )
        self.mu = nn.Linear(2,2)
        self.logvar = nn.Linear(2, 2)
        
        self.decoder = nn.Sequential(
            nn.Linear(2,50),
            nn.ReLU(),
            nn.Linear(50,250),
            nn.ReLU(),
            nn.Linear(250,hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size,input_size),
            # nn.ReLU()
            nn.Sigmoid()
            )

    def compress(self, X):
        # print(X.size())
        out = self.encoder(X)
        # out = t.concat([self.mu(out),self.logvar(out)],axis=1)
        return self.mu(out),self.logvar(out)
    
    def get_means(self,X):
        with t.no_grad():
            self.encoder.train(False)
            means,_,_ = self.compress(X)
            return means
    def decompress(self,X):
        return self.decoder(X)
    
class Vae(Net):
    def __init__(self,input_size,hidden_size,num_classes):
        super(Vae,self).__init__(input_size,hidden_size,num_classes)
    
    def sample(self,X):
        
        means,logvars_ = self.compress(X)
        vars_ = logvars_.exp()
        # means = out[:,:2]
        # vars_ = out[:,2:].exp()
        eps = t.FloatTensor(means.size()).normal_().to(dev)
        
        return means + vars_.sqrt() * eps,means,vars_
    
class Model(Vae):
    def __init__(self,input_size,hidden_size,num_classes):
        super(Model,self).__init__(input_size,hidden_size,num_classes)
        self.to(dev)
    def fit(self, train_loader,epochs,lr,verbose=0):
        self.optimizer = t.optim.Adam(self.parameters(),lr=lr)
        self.encoder.train(mode=True)
        for e in tqdm(range(epochs)):
            #if verbose:
                #print(f'Start epoch {e}.')
                
            for i,(images,labels) in enumerate(train_loader):
                
                # tamaño original [100,1,28,28]
                # tamaño necesitado [100,28*28]
                images = images.reshape(-1,28*28).to(dev)
                # outputs = self(images)
                sample,means,vars_ = self.sample(images)
                # qxz = t.distributions.Normal(self.decompress(sample),t.ones_like(images))
                # ll = qxz.log_prob(images)
                # ll = -0.5*nn.MSELoss(reduction='sum')(self.decompress(sample),images)
                # ll = - 0.5*t.sum((self.decompress(sample) - images)**2,dim=1)
                #ll = nn.BCELoss(reduction='sum')(self.decompress(sample),images)
                ll = ((self.decompress(sample) - images)**2).sum()
                kl =  t.sum(vars_ + means**2 - vars_.log() - 0.5)
                loss =  (ll + kl)
                
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                #if i % 100==0:
                #    print(f'\t[{i}].Loss:{loss}, LL:{ll}, KL:{kl}')

data = example_data
print('Crear la red')
net = Model(input_size,hidden_size,num_classes)
print('Entrenar la red')
data = example_data[None]
net.fit(train_loader,
        epochs=100,
        lr=0.001,
        verbose=1)

# %% See the means

def plot(vector):
    vec = vector.reshape(28,28)
    plt.imshow(vec,cmap='gray')
    plt.show()

f,ax = plt.subplots(1,1)

tar = example_data.reshape(-1,28*28).to(dev)
tar_cpu = example_data.reshape(-1,28*28)
#means = net.get_means(tar)#.detach().numpy()
means,_ = net.compress(tar)
means1 = means.to('cpu').detach().numpy()
ax.scatter(means1[:,0],means1[:,1],c=example_target,s=.1)

reconstructed = net.decompress(t.tensor(means)).to('cpu')
# reconstructed = reconstructed.reshape(-1,28,28)

# %%
i = 30
plot(tar_cpu[i])
plot(reconstructed[i].detach().numpy())
plt.show()

import numpy as np
encoded = np.empty((0,2))
lables = np.empty((0,))
for img,lab in tqdm(train_loader):
  img_cuda = img.reshape(-1,28*28).to('cuda')
  mean,_ = net.compress(img_cuda)
  encoded = np.vstack((encoded,mean.to('cpu').detach().numpy()))
  lables = np.hstack((lables,lab))

plt.scatter(encoded[:,0],encoded[:,1],c=lables) 
a = np.empty((0,2),float)
b=np.zeros((2,2))

def gen_fig(vae,ax=None):
  N = t.distributions.Normal(0,1)
  sample = N.sample((1,2)).to(dev)
  recons = vae.decompress(sample)
  recons_cpu = recons.to('cpu').reshape(28,28).detach().numpy()
  #print(recons_cpu)
  plt.imshow(recons_cpu,cmap='gray')
gen_fig(net)

