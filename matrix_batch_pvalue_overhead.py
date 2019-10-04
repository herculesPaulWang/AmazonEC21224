"""
@Author: Baoqian Wang
@Description: Coded Parallel MPI Matrix Multiplication

"""

from mpi4py import MPI
import sys
import numpy as np
from numpy.linalg import inv
import copy 
from numpy.linalg import matrix_rank
from numpy.linalg import inv
import time

#submatrix = np.zeros(shape=(numberNodes,numberDecoder))
def populateMatrix(nRows, nColumns):
	matrix=np.random.rand(nRows,nColumns)
	return matrix
    
def populateRandomMatrix(nRows, nColumns):
	matrix=np.random.rand(nRows,nColumns)
	return matrix  

def produceGM(total_nRows,minimum_nRows):
	codeMatrix=np.random.rand(int(total_nRows),int(minimum_nRows))
	#x=0.004*np.arange(1,(nRows+1),1)
	#codeMatrix=np.vander(x,nColumns,increasing=True)
	#codeMatrix=codeMatrix.astype('float64')
	return codeMatrix	


comm = MPI.COMM_WORLD
worldSize = comm.Get_size()
rank = comm.Get_rank()
column=2
r=int(sys.argv[1])
elements=int(sys.argv[2])
#pValue=int(sys.argv[3])
num_iteration=int(sys.argv[3])

offset=np.zeros((1,worldSize-1))
pvalue=np.zeros((1,worldSize-1))
for j in range(0,worldSize-1):
	offset[0,j]=int(sys.argv[4+j])
	pvalue[0,j]=int(sys.argv[4+worldSize-1+j])
totalrows=np.sum(offset)
#print(pvalue)
if rank==0:
	H = produceGM (totalrows+100,r)
	A = populateMatrix(r,elements)
	offsetSum=np.cumsum(offset)
	for j in range(1,worldSize-1):
		if(j==1):
			matrixNode=np.zeros(shape=(int(offset[0,j-1]),elements))
			matrixNode=np.matmul(H[0:int(offsetSum[j-1]),:],A)
			comm.send(matrixNode,dest=1,tag=1)
		matrixNode=np.zeros(shape=(int(offset[0,j]),elements))
		matrixNode=np.matmul(H[int(offsetSum[j-1]):int(offsetSum[j]),:],A)
		comm.send(matrixNode,dest=j+1,tag=j+1)

if rank!=0:
	matrixRecv=comm.recv(source=0,tag=rank)

for k in range(num_iteration):
	comm.Barrier()
	time.sleep(1)
	if rank==0:
		x = populateRandomMatrix(elements,column)
		print(0)
		start=MPI.Wtime()
		for j in range(1,worldSize):	
			comm.send(x,dest=j,tag=10*j+k)	

	if rank==1:
		recv_x=comm.recv(source=0,tag=rank*10+k)
		batch_size=int(np.ceil(matrixRecv.shape[0]/pvalue[0,rank-1]))
		for j in range(int(pvalue[0,rank-1]-1)):
			waitT1=MPI.Wtime()
			matrixRes=np.matmul(matrixRecv[j*batch_size:(j+1)*batch_size,:],recv_x)
			waitT2=MPI.Wtime()
			time.sleep(3*(waitT2-waitT1))
			comm.send(matrixRes,dest=0,tag=rank+10*j)
		waitT3=MPI.Wtime()
#		print((pvalue[0,rank-1]-1))
		matrixResFinal=np.matmul(matrixRecv[int((pvalue[0,rank-1]-1))*batch_size:,:],recv_x)
		waitT4=MPI.Wtime()
		time.sleep(3*(waitT4-waitT3))
		comm.send(matrixResFinal,dest=0,tag=rank+80)
	if rank>1:
		recv_x=comm.recv(source=0,tag=rank*10+k)
		batch_size=int(np.ceil(matrixRecv.shape[0]/pvalue[0,rank-1]))
		for j in range(int(pvalue[0,rank-1]-1)):
			waitT1=MPI.Wtime()
			matrixRes=np.matmul(matrixRecv[j*batch_size:(j+1)*batch_size,:],recv_x)
			waitT2=MPI.Wtime()
			#time.sleep(3*(waitT2-waitT1))
			comm.send(matrixRes,dest=0,tag=rank+10*j)
		waitT3=MPI.Wtime()
		matrixResFinal=np.matmul(matrixRecv[int((pvalue[0,rank-1]-1))*batch_size:,:],recv_x)
		waitT4=MPI.Wtime()
		#time.sleep(3*(waitT2-waitT1))
		comm.send(matrixResFinal,dest=0,tag=rank+80)		
	if rank==0:
		status=MPI.Status()
		totalRes=np.zeros((1,column))
		rankSource=[];
		while(1):
			if(totalRes.shape[0]>=totalrows):
				break;
			res=comm.recv(source=MPI.ANY_SOURCE,tag=MPI.ANY_TAG,status=status)	
			totalRes=np.concatenate((totalRes,res),axis=0)
			rankSource.append(status.Get_source())
			tempEnd=MPI.Wtime()
			print(totalRes.shape[0])
			print(tempEnd-start);
		totalRes=np.delete(totalRes,(0),axis=0)
		rankSource=np.asarray(rankSource)
		#end=MPI.Wtime()
		#print(totalRes.shape[0])
		#print(end-start)
