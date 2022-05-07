find /etc -type f -or -type l | while read name; do
   if test -h "$name" ; then
       echo $(realpath $name)
   else
        echo $name
   fi
done
