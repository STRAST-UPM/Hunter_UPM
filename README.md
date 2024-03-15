# Hunter_UPM
Network tool specialized in anycast IP destination tracking, geolocating the destination of packets sent to anycast addresses.

## Citation
This software has been developed as part of our research to uncover cross-border personal data transfers failing to meet the requirements set by the EU General Protection Regulation. Please cite our [paper](http://dx.doi.org/10.2139/ssrn.4627981) instead of referencing the software repository to support our research. You can find a pre-print [here]
<http://dx.doi.org/10.2139/ssrn.4627981>.

## Usage
Hunter traces packets sent from a given source to a destination anycast IP. The source can be your computer or one of the probes offered by [RIPE Atlas](https://atlas.ripe.net/). If you want to use a RIPE Atlas probe as the source the approximate coordinates of the probe must be given (and Hunter will select a  probe close to those coordinates).

Example of usage with an Atlas probe as source
```
python3 main.py -t 34.110.229.214 -o "(48.85341, 2.3488)" -y true -v
```

Example of usage using the host machine as the source
```
python3 main.py -t 34.110.229.214 -y true -v
```

If you have any question on how to use the tool, you can use the help option.
```
python3 main.py -h
```

##License
Hunter is licensed under [Creative Common Attribution-NonCommercial-ShareAlike 4.0 International](http://creativecommons.org/licenses/by-nc-sa/4.0/). You may not use Hunter except in compliance with this license.

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
