import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import numpy as np
import torch
import pickle
import logging
import argparse
import pandas as pd 
from torch.utils.data import DataLoader
from torch.autograd import Variable
from torch.nn import BCEWithLogitsLoss,NLLLoss,CrossEntropyLoss
import torch.nn.functional as F
from baselines.GSCU.predator_prey.embedding_learning.dataset import OpponentVAEDataset
from baselines.GSCU.predator_prey.embedding_learning.opponent_models import Encoder,EncoderVAE,Decoder
from baselines.GSCU.predator_prey.utils.config_predator_prey import Config

logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

# adv_pool = Config.ADV_POOL_SEEN

def kl_divergence(mu, logvar):
    dimension_wise_kld, mean_kld = None, None
    total_kld = torch.mean(-0.5 * torch.sum(1 + logvar - mu ** 2 - logvar.exp(), dim = 1), dim = 0)
    return total_kld, dimension_wise_kld, mean_kld

def get_annealing_schedule(n_repeat, max_bata, n_total_it):
    cycle_size = n_total_it//n_repeat
    print ('cycle_size',cycle_size)
    beta = [i*max_bata/cycle_size for i in range(cycle_size)]
    all_beta = beta * n_repeat 
    if len(all_beta) < n_total_it:
        all_beta += [max_bata/2] * (n_total_it-len(all_beta))
    return all_beta

def main(version):

    data_dir = Config.DATA_DIR
    model_dir = Config.VAE_MODEL_DIR

    train_data_file = data_dir + 'vae_data_' + version + '.p'
    test_data_file = data_dir + 'vae_data_' + version + '_test.p'
    batch_size = 1024
    gpuid = [-1] 
    epochs = 30
    learning_rate = 0.001
    n_repeat = 2
    max_bata = 0.1
    obs_dim = 37
    from baselines.GSCU.predator_prey.utils.config_predator_prey import args as arg
    num_adv_pool = arg.train_pool_size
    action_dim = 5
    hidden_dim = Config.HIDDEN_DIM
    latent_dim = Config.LATENT_DIM
    is_vae = True

    train_dset = OpponentVAEDataset(train_data_file)
    train_data_loader = DataLoader(train_dset,
                              batch_size = batch_size,
                              shuffle = True,
                             )
    test_dset = OpponentVAEDataset(test_data_file)
    test_data_loader = DataLoader(test_dset,
                              batch_size = batch_size,
                              shuffle = False,
                             )
    use_cuda = (len(gpuid) >= 1)
    n_total_it = int((len(train_dset)/batch_size) * epochs)
    beta = get_annealing_schedule(n_repeat, max_bata, n_total_it)

    if is_vae:
        encoder = EncoderVAE(num_adv_pool, hidden_dim, latent_dim)
    else:
        encoder = Encoder(num_adv_pool, hidden_dim, latent_dim)

    decoder = Decoder(obs_dim, hidden_dim, latent_dim, action_dim, output_dim2=None)

    if use_cuda > 0:
        encoder.cuda()
        decoder.cuda()

    recon_loss = CrossEntropyLoss()
    disc_loss = CrossEntropyLoss()
    parameters = list(encoder.parameters()) + list(decoder.parameters())
    optimizer = torch.optim.Adam(parameters, lr=learning_rate)

    for epoch_i in range(0, epochs):
        logging.info("At {0}-th epoch.".format(epoch_i))

        # training
        encoder.train()
        decoder.train()
        train_loss = 0.0
        correct = 0.0
        for it, data in enumerate(train_data_loader, 0):
            data_s,data_a,data_i = data

            if use_cuda:
                data_s,data_a,data_i = Variable(data_s).cuda(),Variable(data_a).cuda(),Variable(data_i).cuda()
            else:
                data_s,data_a,data_i = Variable(data_s),Variable(data_a),Variable(data_i)

            data_i_onehot = F.one_hot(data_i, num_classes=num_adv_pool)

            if is_vae:
                embedding,mu,logvar = encoder(data_i_onehot.float())
                kl_loss,_,_ = kl_divergence(mu, logvar)
                mu = mu.cpu().detach().numpy()
                logvar = logvar.cpu().detach().numpy()
                var = np.exp(logvar/2)
                mu_mean = mu
                var_mean = var
                batch_bas_mean_mu = np.mean(np.abs(mu_mean), axis=0)
                batch_bas_mean_var = np.mean(np.abs(var_mean), axis=0)
            else:
                embedding = encoder(data_i_onehot.float())

            probs = decoder(data_s, embedding)

            im_loss = recon_loss(probs,data_a)

            beta_val = beta[epoch_i*int(len(train_dset)/batch_size)+it]

            if is_vae:
                loss = im_loss + beta_val*kl_loss
            else:
                loss = im_loss

            train_loss += loss.data
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            pred = probs.data.max(1, keepdim=True)[1] 
            correct += pred.eq(data_a.data.view_as(pred)).cpu().sum()

        train_avg_loss = train_loss / (len(train_dset) / batch_size)
        train_avg_loss = train_avg_loss.cpu().detach().numpy()
        training_accuracy = (correct.detach().numpy() / len(train_dset))
        logging.info("Average training loss value per instance is {0}, acc is {1} at the end of epoch {2}".format(train_avg_loss, training_accuracy, epoch_i))

        ################################################
        # testing
        encoder.eval()
        decoder.eval()
        test_loss = 0.0
        correct = 0.0

        for it, data in enumerate(test_data_loader, 0):
            data_s,data_a,data_i = data

            if use_cuda:
                data_s,data_a,data_i = Variable(data_s).cuda(),Variable(data_a).cuda(),Variable(data_i).cuda()
            else:
                data_s,data_a,data_i = Variable(data_s),Variable(data_a),Variable(data_i)
            data_i_onehot = F.one_hot(data_i, num_classes=num_adv_pool)

            if is_vae:
                embedding,mu,logvar = encoder(data_i_onehot.float())
                kl_loss,_,_ = kl_divergence(mu, logvar)
            else:
                embedding = encoder(data_i_onehot.float())

            # here in testing, use mean instead of embedding
            probs = decoder(data_s, mu)
            im_loss = recon_loss(probs,data_a)

            beta_val = beta[epoch_i*int(len(train_dset)/batch_size)+it]

            if is_vae:
                loss = im_loss + beta_val*kl_loss
            else:
                loss = im_loss
            test_loss += loss.data
            pred = probs.data.max(1, keepdim=True)[1] 
            correct += pred.eq(data_a.data.view_as(pred)).cpu().sum()

        test_avg_loss = test_loss / (len(test_dset) / batch_size)
        test_avg_loss = test_avg_loss.cpu().detach().numpy()
        test_accuracy = (correct.detach().numpy() / len(test_dset))
        logging.info("Average testing loss value per instance is {0}, acc is {1} at the end of epoch {2}".format(test_avg_loss, test_accuracy, epoch_i))
    

    if is_vae:
        torch.save(encoder.state_dict(), model_dir+'encoder_vae_param_'+version+'_'+str(epoch_i)+'.pt')
    else:
        torch.save(encoder.state_dict(), model_dir+'encoder_ae_param_'+version+'_'+str(epoch_i)+'.pt')
    torch.save(decoder.state_dict(),  model_dir+'decoder_param_'+version+'_'+str(epoch_i)+'.pt')



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=None)
    parser.add_argument('-v', '--version', default='v0')
    args = parser.parse_args()
    main(args.version)
