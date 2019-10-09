import os
import sys
import time
import threading

from cloudify_rest_client import CloudifyClient
from cloudify_rest_client.exceptions import DeploymentEnvironmentCreationInProgressError
from cloudify_rest_client.exceptions import DeploymentEnvironmentCreationPendingError

endpoint_dict = {"rest_endpoint":'10.239.0.220',"rest_endpoint_port":5000}
blueprint_id = 'Counter-Test-BP'
deployments_list = []
errors_list = []
deployments_count = 0
max_threads = 0
currently_executing = 0
current_workflows_count = 0

current_milli_time = lambda: int(round(time.time() * 1000))

def get_workflow_status(client,deployment_id):
        status = 'terminated'
        executions = client.executions.list(deployment_id,_include=['status'])
        for execution in executions:
		if execution['status']=='started' or execution['status']=='pending':
			status = execution['status']
			break
	else:
		status = 'terminated'
        return status

def increment_executions(lock):
	global deployments_count
	global currently_executing
	lock.acquire()
	deployments_count = deployments_count - 1 
        currently_executing = currently_executing + 1
	lock.release()

def decrement_executions(client,deployment_id,lock):
	global currently_executing
	while get_workflow_status(client,deployment_id)!='terminated':
		time.sleep(0.5)
        lock.acquire()
        currently_executing = currently_executing - 1
        lock.release()


def create_run_deployment(client,endpoint_dict,lock):
	global currently_executing
	try:
		deployment_id = 'Counter-Test-DT'+str(current_milli_time())
		print ('time start for deployment {0} is {1}'.format(deployment_id,str(time.strftime('%Y/%m/%d %H:%M:%S'))))
		deployment = client.deployments.create(blueprint_id,deployment_id,endpoint_dict)
		for attempt in range(50):
			try:
				execution = client.executions.start(deployment_id,'install')
			except DeploymentEnvironmentCreationInProgressError as inprogress:
				time.sleep(0.2)
			except DeploymentEnvironmentCreationPendingError as pending:
				time.sleep(0.2)
			except Exception as ex:
				print ("error happned for deployment {0} exception {1}".format(deployment_id,str(ex)))
				errors_list.append(deployment_id)
				decrement_executions(client,deployment_id,lock)
				break
			else:
				deployments_list.append(deployment_id)
				print ('time finish for successful deployment {0} is {1}'.format(deployment_id,str(time.strftime('%Y/%m/%d %H:%M:%S'))))
				decrement_executions(client,deployment_id,lock)
				break
		else:
			print ("deployment {0} timed-out ".format(deployment_id))
			decrement_executions(client,deployment_id,lock)
			errors_list.append(deployment_id)
	except Exception as ex:
		decrement_executions(client,deployment_id,lock)
		print ("error happned for deployment {0} exception {1}".format(deployment_id,str(ex)))
		errors_list.append(deployment_id)

def create_threads(threads,client,endpoint_dict,lock):
	global deployments_count
	global max_threads
	global currently_executing
	for i in range(deployments_count):
		while currently_executing == max_threads:
			time.sleep(1)
		increment_executions(lock)
               	x = threading.Thread(target=create_run_deployment, args=(client,endpoint_dict,lock))
               	threads.append(x)
               	x.start()

def destroy_threads(threads,lock):
	global deployments_count
	executionDone = False
	while not executionDone:
		lock.acquire()
		executionDone = (deployments_count == 0)
		lock.release()
		time.sleep(1)
	threads = [t for t in threads if t.is_alive()]
	for index, thread in enumerate(threads):
		thread.join()

if __name__=='__main__':
	client = CloudifyClient(host='10.239.0.215',username='admin',password='admin',tenant='default_tenant')
	deployments_count=int(sys.argv[1])
	max_threads=int(sys.argv[2])
	threads=[]
	lock = threading.Lock()
	print("Max Threads {0}".format(max_threads))
	for i in range(max_threads):
		create_threads(threads,client,endpoint_dict,lock)

	destroy_threads(threads,lock)
	time.sleep(1)
	print ("Deployments List Legnth {0}".format(len(deployments_list)))
	print ("Errors List Legnth {0}".format(len(errors_list)))
