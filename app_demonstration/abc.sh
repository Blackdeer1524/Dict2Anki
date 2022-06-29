for i in *-*; do
    mv -- "$i" "${i//-/_}"
done
