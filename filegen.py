#!/usr/bin/python

import os

class filegen:
       
    # Write random sequence of bytes to an output file at the specified path.
    def gen_rand(self, fpath, size):
        try:
            with open(fpath, 'wb') as f:
                randbytes = os.urandom(size)
                f.write(randbytes)
            print("Successful random file generation at '{0}'.".format(fpath)) 
        except Exception as e:
            print("Exception while outputing random file at '{0}': '{1}'".format(fpath, e))

    # Write a predictable sequence of text to an output file at the specified path.
    def gen_text(self, fpath, txt, cnt=1):
        try:
            with open(fpath, 'w') as f:
                for i in range(0, cnt): 
                    f.write(txt)
            print("Successful text file generation at '{0}'.".format(fpath)) 
        except Exception as e:
            print("Exception while outputing text file at '{0}': '{1}'".format(fpath, e))

if __name__ == "__main__":
    fg = filegen()
    
    binfile = "./test_filegen{0}.bin"
    for i in range(0, 4):
        fg.gen_rand(binfile.format(i+1), 256)
    
    txtfile = "./test_filegen{0}.txt"
    for i in range(0, 4):
        fg.gen_text(txtfile.format(i+1), "f00f", 64)
