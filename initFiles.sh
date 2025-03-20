#!/bin/bash

mkdir -p Outputs # Creates Outputs directory

# List of required files
FILES=(
    "runEncOutRef.txt"
    "runEncOutProp.txt"
    "runCompOutRef.txt"
    "runCompOutProp.txt"
    "runDecOutRef.txt"
    "runDecOutProp.txt"
    "runTotalOutRef.txt"
    "runTotalOutProp.txt"
    "commGeoOutRef.txt"
    "commGeoOutProp.txt"
    "commCarerOutRef.txt"
    "commCarerOutProp.txt"
    "scaleRunOutRef.txt"
    "scaleRunOutProp.txt"
    "scaleThroughputOutRef.txt"
    "scaleThroughputOutProp.txt"
    "scaleLatencyOutRef.txt"
    "scaleLatencyOutProp.txt"
    "securityRunOutRef.txt"
    "securityRunOutProp.txt"
    "securityOverOutRef.txt"
    "securityOverOutProp.txt"
)

# Loop through and create files
for file in "${FILES[@]}"; 
do
    > "Outputs/$file"
done

echo "All required files exist proceed to run the docker compose command."
