from socket import *
import time
import binascii

serverPort = 5300
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))
print("The server is ready to receive")
# 存储请求的NAME和TYPE, 响应, ttl, time, 实现缓存
req = []
resp = []
ttls = []
times = []

while True:
    requestMessage, clientAddress = serverSocket.recvfrom(2048)
    startIndex = 12
    # 根据域名以\x00结尾的特点, 找到到请求的域名和请求类型
    while True:
        if requestMessage[startIndex] == 0:
            break
        else:
            startIndex = startIndex + 1
    endIndex = startIndex
    Qname = requestMessage[12:endIndex+1]
    QnameType = requestMessage[12:endIndex+3]
    # 通过域名和类型判断缓存中是否有相同的请求
    if req.count(QnameType) != 0:
        # 若存在, 则判断TTL是否有效
        ticks = time.time()
        ID = requestMessage[0:2]
        currentTTL = ttls[req.index(QnameType)]
        currentTime = times[req.index(QnameType)]
        if ticks - currentTime <= currentTTL:
            # 若TTL有效, 则将ID更换成新的ID, 并将TTL减去经过的时间后, 将缓存中的响应发送给客户端
            newTTLs = []
            ttlIndexs = []
            oldMessage = resp[req.index(QnameType)]
            hexnum = str(binascii.b2a_hex(oldMessage[6:8]))[2: -1]
            numberOfAnswer = int(hexnum, 16)
            hex1 = str(binascii.b2a_hex(oldMessage[endIndex + 11:endIndex + 15]))[2: -1]
            oldttl1 = int(hex1, 16)
            newTTL1 = oldttl1 - int(ticks) + currentTime
            newTTLs.append((int(newTTL1)).to_bytes(4, byteorder='big'))
            ttlIndexs.append(endIndex + 11)
            # 根据DLength找到所有TTL的位置
            hexdlength = str(binascii.b2a_hex(oldMessage[endIndex + 15:endIndex + 17]))[2: -1]
            dLength = int(hexdlength, 16)
            ttlIndex = endIndex + 17 + dLength + 6
            for i in range(numberOfAnswer - 1):
                hexttl = str(binascii.b2a_hex(oldMessage[ttlIndex:ttlIndex + 4]))[2: -1]
                ttl = int(hexttl, 16)
                newttl = ttl - int(ticks) + currentTime
                newTTLs.append((int(newttl)).to_bytes(4, byteorder='big'))
                ttlIndexs.append(ttlIndex)
                hexdlength = str(binascii.b2a_hex(oldMessage[ttlIndex + 4:ttlIndex + 6]))[2: -1]
                dLength = int(hexdlength, 16)
                ttlIndex = ttlIndex + 6 + dLength + 6
            newresponse = ID
            index = 2
            for i in range(numberOfAnswer):
                newresponse = newresponse + resp[req.index(QnameType)][index:ttlIndexs[i]] + newTTLs[i]
                index = 4 + ttlIndexs[i]
            newresponse = newresponse + resp[req.index(QnameType)][index:len(resp[req.index(QnameType)])]
            serverSocket.sendto(newresponse, clientAddress)
        else:
            # 若TTL失效, 则将请求发送给上游服务器
            serverSocket.sendto(requestMessage, ("8.8.8.8", 53))
            # 从上游服务器收到响应信息
            responseMessage, upStreamServerAddress = serverSocket.recvfrom(2048)
            hexnum = str(binascii.b2a_hex(responseMessage[6:8]))[2: -1]
            numberOfAnswer = int(hexnum, 16)
            hex1 = str(binascii.b2a_hex(responseMessage[endIndex + 11:endIndex + 15]))[2: -1]
            minTTL = int(hex1, 16)
            # 根据DLength找到所有TTL的位置, 并找到其中的最小值
            hexdlength = str(binascii.b2a_hex(responseMessage[endIndex + 15:endIndex + 17]))[2: -1]
            dLength = int(hexdlength, 16)
            ttlIndex = endIndex + 17 + dLength + 6
            for i in range(numberOfAnswer - 1):
                hexttl = str(binascii.b2a_hex(responseMessage[ttlIndex:ttlIndex + 4]))[2: -1]
                ttl = int(hexttl, 16)
                if ttl < minTTL:
                    minTTL = ttl
                hexdlength = str(binascii.b2a_hex(responseMessage[ttlIndex + 4:ttlIndex + 6]))[2: -1]
                dLength = int(hexdlength, 16)
                ttlIndex = ttlIndex + 6 + dLength + 6
            # 把缓存中相应的ttl, 当前时间, 响应进行更新
            ttls[req.index(QnameType)] = minTTL
            times[req.index(QnameType)] = time.time()
            resp[req.index(QnameType)] = responseMessage
            # 把响应信息发送给客户端
            serverSocket.sendto(responseMessage, clientAddress)
    else:
        # 若缓存中没有该请求, 则将请求发送给上游服务器
        req.append(QnameType)
        serverSocket.sendto(requestMessage, ("8.8.8.8", 53))
        # 从上游服务器收到响应信息
        responseMessage, upStreamServerAddress = serverSocket.recvfrom(2048)
        hexnum = str(binascii.b2a_hex(responseMessage[6:8]))[2: -1]
        numberOfAnswer = int(hexnum, 16)
        hex1 = str(binascii.b2a_hex(responseMessage[endIndex + 11:endIndex + 15]))[2: -1]
        minTTL = int(hex1, 16)
        # 根据DLength找到所有TTL的位置, 并找到其中的最小值
        hexdlength = str(binascii.b2a_hex(responseMessage[endIndex+15:endIndex+17]))[2: -1]
        dLength = int(hexdlength, 16)
        ttlIndex = endIndex + 17 + dLength + 6
        for i in range(numberOfAnswer - 1):
            hexttl = str(binascii.b2a_hex(responseMessage[ttlIndex:ttlIndex+4]))[2: -1]
            ttl = int(hexttl, 16)
            if ttl < minTTL:
                minTTL = ttl
            hexdlength = str(binascii.b2a_hex(responseMessage[ttlIndex+4:ttlIndex+6]))[2: -1]
            dLength = int(hexdlength, 16)
            ttlIndex = ttlIndex + 6 + dLength + 6
        # 把相应的ttl, 当前时间, 响应存进缓存中
        ttls.append(minTTL)
        times.append(time.time())
        resp.append(responseMessage)
        # 把响应信息发送给客户端
        serverSocket.sendto(responseMessage, clientAddress)
