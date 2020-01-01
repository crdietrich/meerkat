# main.py -- put your code here!
from meerkat import relay
from meerkat.base import time

r = relay.Single(0, 0x18, "json")

print("Status: {}".format(r.get_status()))
print("---")

r.off()
print("Relay set to off")
print("Status: {}".format(r.get_status()))
print("---")
time.sleep(1)

r.on()
print("Relay set to on")
print("Status: {}".format(r.get_status()))
print("---")

for n in range(5):
    r.toggle(verbose=True)
    r.write(description="toggle {}".format(n))
    print("---")
    time.sleep(1)
