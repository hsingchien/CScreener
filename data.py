from scipy.io import loadmat
from scipy.ndimage import center_of_mass
import numpy as np
import warnings
from typing import List


class MS:
    def __init__(self, ms_file=None):
        self.deftFiltTraces = np.zeros((10, 10))
        self.deftRawTraces = np.zeros((10, 10))
        self.deftSpikes = np.zeros((10, 10))
        self.deftROIs = np.zeros((10, 10))
        self.deftLabels = np.ones((10, 1))
        self.deftNumNeurons = 0
        self.NeuronList = []
        # If path to ms.mat is fed in the contructor, construct accordingly
        if ms_file:
            self.FiltTraces = ms_file.FiltTraces
            self.RawTraces = ms_file.RawTraces
            self.Spikes = ms_file.S
            self.ROIs = ms_file.SFPs
            self.NumNeurons = np.squeeze(ms_file.numNeurons)
            if hasattr(ms_file, "cell_label"):
                self.Labels = ms_file.cell_label.flatten()
            else:
                self.Labels = np.ones(ms_file.FiltTraces.shape[1])

            # Construct list of Neuron objects
            for i in range(self.NumNeurons):
                FiltTrace = self.FiltTraces[:, i]
                RawTrace = self.RawTraces[:, i]
                Spike = self.Spikes[i, :]
                ROI = self.ROIs[:, :, i]
                Label = self.Labels[i]
                # Construct Neuron, ID starting from 1
                self.NeuronList.append(
                    Neuron(FiltTrace, RawTrace, Spike, ROI, Label, i + 1)
                )

            self.dist_map = self.distance_map()

        else:
            self.FiltTraces = self.deftFiltTraces
            self.RawTraces = self.deftFiltTraces
            self.Spikes = self.deftSpikes
            self.ROIs = self.deftROIs
            self.NumNeurons = self.deftNumNeurons
            self.CellLabel = self.deftLabels

    def hasNeuron(self):
        if self.NumNeurons > 0:
            return True
        else:
            return False

    def distance_map(self):
        dist_map = np.zeros((self.NumNeurons, self.NumNeurons))
        for i in range(self.NumNeurons):
            for j in range(i, self.NumNeurons):
                neuron_i_center = self.NeuronList[i].get_center()
                neuron_j_center = self.NeuronList[j].get_center()
                dist_map[i, j] = np.linalg.norm(neuron_i_center - neuron_j_center)
                dist_map[j, i] = dist_map[i, j]
        return dist_map

    def get_cell_labels(self):
        cell_labels = np.zeros(self.NumNeurons)
        cell_labels[[i.Label for i in self.NeuronList]] = 1
        return cell_labels


class Neuron:
    def __init__(
        self,
        FiltTrace=np.ndarray,
        RawTrace=np.ndarray,
        Spike=np.ndarray,
        ROI=np.ndarray,
        Label=int,
        ID=int,
    ):
        self.FiltTrace = FiltTrace
        self.RawTrace = RawTrace
        self.Spike = Spike
        self.ROI = ROI
        self._Label = Label > 0
        self.ID = ID
        self.Visible = True
        self.center = np.array(center_of_mass(self.ROI))

    @property
    def Label(self):
        return "Good" if self._Label else "Bad"

    @Label.setter
    def Label(self, value):
        self._Label = value > 0

    def is_good(self):
        return self._Label

    def get_max_filt_frame(self):
        return np.argmax(self.FiltTrace)

    def get_max_raw_frame(self):
        return np.argmax(self.RawTrace)

    def set_good(self):
        self.Label = 1

    def set_bad(self):
        self.Label = 0

    def toggle_label(self):
        if self.Label == 0:
            self.Label = 1
        else:
            self.Label = 0

    def get_center(self):
        return self.center

    def get_ROI(self):
        return self.ROI

    def get_FiltTrace(self):
        return self.FiltTrace

    def get_RawTrace(self):
        return self.RawTrace

    def get_ID(self):
        return self.ID


class NeuronGroup(object):
    def __init__(self, neuron_list: List = []) -> None:
        # Use neuron.ID as key and return pointer to the neuron
        self.neuron_dict = dict()
        self.generate_neuron_dict(neuron_list)

    def generate_neuron_dict(self, neuron_list):
        for neuron in neuron_list:
            self.add_neuron(neuron)

    def add_neuron(self, neuron):
        if not neuron:
            return False
        if not self.neuron_dict.get(neuron.ID):
            self.neuron_dict[neuron.ID] = neuron
        else:
            warnings.warn("Neuron ID already exists")

    def pop_neuron(self, neuron):
        return self.neuron_dict.pop(neuron.ID, None)

    def contour_items(self):
        contour_items = []
        for key in self.neuron_dict.keys():
            contour_items.append(self.neuron_dict[key].ROI_Item)

    def setVisible(self, visible: bool = True):
        for key in self.neuron_dict.keys():
            self.neuron_dict[key].ROI_Item.setVisible(visible)

    def is_in(self, neuron):
        if self.neuron_dict.get(neuron.ID):
            return True
        else:
            return False
