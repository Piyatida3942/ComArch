# 0 < n < 27

def nCkNoMulDiv(n,k):
    """
    Calculating nCk without using multiplication and division
    #  n!/((n-k)!k!)   = n!/(a!*b!) when a = min(k, n-k) and b = max(k, n-k)
    """
    
    n_k = n-k
    if k < n_k:
        a,b = k,n_k
    else:
        a,b = n_k,k
    if k==n:
        return 1
    else:               #find n * n-1 * n-2 * ... * b+1  = n!/b!
        nCk=n
        for i in range(n-1,b,-1):
            tmp = 0
            for j in range(i):
                tmp += nCk
            nCk = tmp


    faca = 1            #find a!
    for i in range(2,a+1):
            tmp = 0
            for j in range(i):
                tmp += faca
            faca = tmp
    
    if faca > 1:        #find (n!/b!) /a!  using sumation instead of division
        tmm=faca
        result=1
        while tmm < nCk:
            tmm += faca
            result+=1
        nCk = result
    return nCk

import math
d={} # dictionary collect all 
stop = False
for n in range(1,26+1):
    if stop: break
    for k in range(1,n+1):
        nCk = int(math.factorial(n)/(math.factorial(n-k)*math.factorial(k)))
        nCk2 = nCkNoMulDiv(n,k)
        print(n,k,nCk)
        if (nCk != nCk2 ):
            print(n, k, nCk, nCk2,"FALSE")
            stop =True
        if nCk in d:
            d[nCk].append((n,k))
        else:
            d[nCk] = [(n,k)]

print(max(d))      #10400600
print(hex(max(d))) #0x9eb358


