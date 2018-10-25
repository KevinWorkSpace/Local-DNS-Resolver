
import dns.resolver

a = dns.resolver.query("www.163.com", 'a', "IN", True)
for i in a.response.answer:
    for j in i.items:
        print(j)

a = dns.resolver.query("www.163.com", 'a')
for i in a.response.answer:
    for j in i.items:
        print(j)