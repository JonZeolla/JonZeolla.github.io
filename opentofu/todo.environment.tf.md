# Pick a supported AZ for the Cloud9 instance dynamically

Consider a wrapper shell script to set and pass in as a var or local.

```terraform
resource "null_resource" "pick_cloud9_az" {
  #  provisioner "local-exec" {
  #    command = <<EOF
  # Testing: valid_availability_zones=($(aws ec2 describe-instance-type-offerings --location-type availability-zone --region "us-east-1" --query
# "InstanceTypeOfferings[?InstanceType=='t3.xlarge'].[Location]" | jq -r '.[].[]'))
        valid_availability_zones=($(aws ec2 describe-instance-type-offerings --location-type availability-zone --region "${var.region}" --query "InstanceTypeOfferings[?InstanceType=="${var.cloud9_instance_type}"].[Location]" | jq -r ".[].[]"))
        num_azs="${#valid_availability_zones[@]}"
        random_index="$((RANDOM % num_azs))"
        availability_zone="${az_array[random_index]}"
  #    EOF
  #  }
}
# TODO: Pick an AZ and pass it in as a variable using the specified region; do in a null_resource so we can use var.region
# Pick one and pass it in
# IFS=$'\n' read -r -a az_array <<< "$valid_availability_zones"
#
# # Get the number of available availability zones
# num_azs=${#az_array[@]}
#
# # Generate a random index within the range of available zones
# random_index=$((RANDOM % num_azs))
#
# # Pick a random availability zone
# selected_az="${az_array[random_index]}"
```
