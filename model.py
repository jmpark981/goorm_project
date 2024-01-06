import numpy as np
import pandas as pd
import torch, re
import torch.nn as nn
from transformers import ElectraModel


class BertCNNClassifier(nn.Module):     #Electra(Small)+CNN(1D)
    def __init__(self, model_name):
        super(BertCNNClassifier, self).__init__()
        self.bert=ElectraModel.from_pretrained(model_name)
        self.hidden_size=self.bert.config.hidden_size
        self.max_length=32

        self.conv1_layers=nn.ModuleList([   #1D CNN을 Bert 뒤에 결합
            nn.Sequential(
              nn.Conv1d(in_channels=self.hidden_size, out_channels=100, kernel_size=k, padding='valid', stride=1),
              nn.ReLU(),
              nn.MaxPool1d(kernel_size=self.max_length-k+1)   #GlobalMaxPooling을 하기 위해 kernel_size를 sequence_len-filter+1로 설정
            ) for k in range(2, 5)    #filter size는 2~4까지
        ])

        self.dropout1=nn.Dropout(p=0.5)     #overfit 방지하기 위해 0.5로 높게 줌
        self.linear1=nn.Linear(6*100, 1)    #각각 3개의 필터(2~4)*2번씩 촐 100개의 필터 이용하므로 600*1(모델 변형)
        self.batchnorm1=nn.BatchNorm1d(1)
        self.sigmoid=nn.Sigmoid()

    def forward(self, input_ids, attention_mask=None, token_type_ids=None):
        outputs=self.bert(input_ids=input_ids, attention_mask=attention_mask)
        x=outputs[0]
        x=x.permute(0, 2, 1)    #pytorch와 맡게 설정하기 위해 transpose 진행

        layer_outputs=[]
        for layer in self.conv1_layers:
            out1=layer(x)
            out2=layer(x)
            layer_outputs.extend((out1, out2))

        out=torch.cat(layer_outputs, dim=1)
        x=self.dropout1(out)
        x=x.view(x.size(0), -1)   #shape: (batch_size, 나머지)
        x=self.linear1(x)
        x=self.batchnorm1(x)
        return self.sigmoid(x)