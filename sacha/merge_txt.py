"""find all barcodes in pairtree and merge pages in txt"""
import glob
from pypairtree import pairtree

DOWNLOADSDIR = 'adocoredownloads'
TARGETDIR = 'books'

PATHS = pairtree.findObjects(DOWNLOADSDIR)

for path in PATHS:
    print(path)
    barcode = path.replace(DOWNLOADSDIR, '').replace('abo', '').replace('/', '').replace('^2b', '+')
    with open('%s/%s.txt' % (TARGETDIR, barcode[1:]), 'w', encoding='utf-8') as fulltext:
        for filename in glob.iglob(path + '/*.txt'):
            print(filename)
            txtfile = open(filename, "r")
            fulltext.write(txtfile.read())
            fulltext.write('\n')
