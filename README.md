# Hunter_UPM
Network tool specialized on anycast IP destination tracking

## Citation
This software repository has the code used to generate the results and 
replication package for this 
[scientific paper](http://dx.doi.org/10.2139/ssrn.4627981). If you are going to
use this in any scientific research cite the paper:
<http://dx.doi.org/10.2139/ssrn.4627981>

## Usage
Hunter can be used running the starting measurement from your computer or using
a RIPE probe as origin. If you want to use a RIPE Atlas probe just use an 
origin and the tool will select one probe near to the point.

Example of usage with origin
```
python3 main.py -t 34.110.229.214 -o "(48.85341, 2.3488)" -y true -v
```

Example of usage using the host machine as the origin
```
python3 main.py -t 34.110.229.214 -y true -v
```

If you have any question on how to use the tool, you can use the help option.
```
python3 main.py -h
```