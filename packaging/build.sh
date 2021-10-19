#!/bin/bash

build_dir=$1
dest_dir=$2

cp ${build_dir}/packaging/debian/* ${dest_dir}/DEBIAN/

cd ${build_dir}
mkdir -p ${dest_dir}/usr/bin
cp -f src/fog_cli.py ${dest_dir}/usr/bin/ || exit
chmod +x ${dest_dir}/usr/bin/fog_cli.py || exit
cp -f src/fog_log_flight.sh ${dest_dir}/usr/bin/ || exit
chmod +x ${dest_dir}/usr/bin/fog_log_flight.sh || exit
cp -f src/fogsw_package_list.sh ${dest_dir}/usr/bin/ || exit
chmod +x ${dest_dir}/usr/bin/fogsw_package_list.sh || exit
cp -f src/mesh_installation_check.sh ${dest_dir}/usr/bin/ || exit
chmod +x ${dest_dir}/usr/bin/mesh_installation_check.sh || exit
