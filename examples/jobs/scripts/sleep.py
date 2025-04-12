from time import sleep, time


print("Sleeping for 10 seconds")
start = time()
sleep(10)
print(f"Done sleeping in {time() - start} seconds")
