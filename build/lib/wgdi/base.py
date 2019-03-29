import configparser
import os
import re

import pandas as pd
import wgdi
from Bio import Seq, SeqIO, SeqRecord


def config():
    conf = configparser.ConfigParser()
    conf.read(os.path.join(wgdi.__path__[0], 'conf.ini'))
    return conf.items('ini')


def load_conf(file, section):
    conf = configparser.ConfigParser()
    conf.read(file)
    return conf.items(section)


def read_colinearscan(file):
    data, b, flag = [], [], 0
    with open(file) as f1:
        for line in f1.readlines():
            line = line.strip()
            if re.match(r"MAXIMUM GAP", line):
                continue
            if re.match(r"the", line):
                b = []
                flag = 1
                continue
            if flag == 0:
                continue
            if re.match(r"\>LOCALE", line):
                flag = 0
                if len(b) == 0:
                    continue
                p = re.split(':', line)
                data.append([b, p[1]])
                b = []
            a = re.split(r"\s", line)
            b.append(a)
    return data


def read_mcscanx(fn):
    f1 = open(fn)
    data, b = [], []
    flag = 0
    for line in f1.readlines():
        line = line.strip()
        if re.match(r"## Alignment", line):
            flag = 1
            if len(b) == 0:
                b.append([line])
                continue
            data.append(b)
            b = []
            b.append([line])
            continue
        if flag == 0:
            continue
        if re.match(r'#', line):
            continue
        a = re.split(r"\:", line)
        c = re.split(r"\s+", a[1])
        b.append([c[1], c[2]])
    data.append(b)
    return data


def read_ks(file):
    ks = pd.read_csv(file, sep='\t', header=None)
    ks = ks.drop_duplicates()
    ks = ks[ks[3] > 0]
    ks.index = ks[0]+','+ks[1]
    return ks


def get_median(data):
    if len(data) == 0:
        return None
    data.sort()
    half = len(data) // 2
    return (data[half] + data[~half]) / 2


def cds_to_pep(cds_file, pep_file, fmt='fasta'):
    records = list(SeqIO.parse(cds_file, fmt))
    for k in records:
        k.seq = k.seq.translate()
    SeqIO.write(records, pep_file, 'fasta')
    return True


def tendem(chr1, chr2, loc1, loc2):
    if (chr1 == chr2) and (abs(float(loc1)-float(loc2)) < 200):
        return True
    return False


def newblast(file, score, evalue, gene_loc1, gene_loc2):
    blast = pd.read_csv(file, sep="\t", header=None)
    blast = blast[(blast[11] >= score) & (
        blast[10] < evalue) & (blast[1] != blast[0])]
    blast = blast[(blast[0].isin(gene_loc1)) & (blast[1].isin(gene_loc2))]
    blast.drop_duplicates(subset=[0, 1], keep='first', inplace=True)
    return blast


def newgff(file):
    gff = pd.read_csv(file, sep="\t", header=None)
    gff.rename(columns={0: 'chr', 1: 'id', 2: 'start',
                        3: 'end', 5: 'order'}, inplace=True)
    gff['chr'] = gff['chr'].astype(str)
    gff['id'] = gff['id'].astype(str)
    gff['start'] = gff['start'].astype(float)
    gff['start'] = gff['end'].astype(float)
    gff['order'] = gff['order'].astype(int)
    return gff


def newlens(file, position):
    lens = pd.read_csv(file, sep="\t", header=None, index_col=0)
    lens.index = lens.index.astype(str)
    if position == 'order':
        lens = lens[2]
    if position == 'end':
        lens = lens[1]
    return lens


def gene_location(gff, lens, step, position):
    loc_gene, dict_chr, n = {}, {}, 0
    for i in lens.index:
        dict_chr[i] = n
        n += lens[i]
    for k in gff.index:
        if gff.loc[k, 'chr'] not in dict_chr:
            continue
        loc = (dict_chr[gff.loc[k, 'chr']] + gff.loc[k, position]) * step
        loc_gene[gff.loc[k, 'id']] = loc
    return loc_gene

def dotplot_frame(fig,ax,lens1,lens2,step1,step2):
    for k in lens1.cumsum()[:-1]*step1:
        ax.axhline(y=k, alpha=1, color='black', lw=0.5)
    for k in lens2.cumsum()[:-1]*step2:
        ax.axvline(x=k, alpha=1, color='black', lw=0.5)
    align = dict(family='Times New Roman', style='normal',
                horizontalalignment="center", verticalalignment="center")
    # yticks = lens1.cumsum()*step1-0.5*lens1*step1
    # plt.yticks(yticks.values, lens1.index, fontsize=12, **align)
    ax.set_xticks([0,0.5,1]) 
    ax.set_xticklabels([1,4,5], fontsize=12)
    # xticks = lens2.cumsum()*step2-0.5*lens2*step2
    # fig.xticks(xticks.values, lens2.index, fontsize=12, **align)
    ax.xaxis.set_ticks_position('none')
    ax.yaxis.set_ticks_position('none')
    ax.axis([0, 1, 1, 0])
    ax.set_ylabel("Test title",labelpad = 12.5,fontsize=18, **align)
    fig.suptitle('Test title', fontsize=18, **align)
    # return xticks, yticks

# if __name__ == "__main__":
#     config()
