cfy deployments list | grep Counter-Test | awk '{print $2}' > deployments.txt
while read p; do
  cfy executions start uninstall -d $p --force --allow-custom-parameters -p ignore_failure=true --timeout 10
  cfy deployments delete $p 
done <deployments.txt
rm -rf deployments.txt
