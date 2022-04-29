from keras.models import load_model
from AnalysisWindow import AnalysisWindow
import numpy as np
import h5py
from ModelHandler import ModelHandler
from PostProcessing import PostProcessing
import matplotlib.pyplot as plt

class CheckFullSignal:
    def __init__(self, configs):
        self.m_configs = configs
        self.m_ngrids = configs["N_GRIDS"]
        self.m_signalBaseLength = configs["SIGNAL_BASE_LENGTH"]
        self.m_marginRatio = configs["MARGIN_RATIO"]
        self.postProcessing = PostProcessing(configs)

    # def load_data(self, folderPath):
    #     arq = h5py.File("Synthetic_2_iHall.hdf5", "r")

    #     x = np.array(arq["i"])
    #     ydet = np.array(arq["events"])
    #     yclass = np.array(arq["labels"])

    #     arq.close()

    def checkSignal(self, x, ydet, yclass, model, scaler):            
            title = ""
            for lab in yclass:
                if title == "":
                    title = title + str(lab)
                else:
                    title = title + ", " + str(lab)
            
            title = "Correct Loads: [" + title + "]\nIdentified Loads: ["

            windows = []
            for i in range(self.m_ngrids):
                windows.append(AnalysisWindow(i * round(self.m_signalBaseLength / self.m_ngrids) + int(self.m_marginRatio * self.m_signalBaseLength), config=self.m_configs))
                windows[i].setTotalAnalysis(self.m_ngrids - 1 + i)

            y_res = np.zeros((x.shape[0], 1))
            for i in range(0, x.shape[0] - self.m_signalBaseLength - 2 * int(self.m_marginRatio * self.m_signalBaseLength), round(self.m_signalBaseLength / self.m_ngrids)):
                x_cut = x[i:i + self.m_signalBaseLength + 2 * int(self.m_marginRatio * self.m_signalBaseLength)]
                x_cut = np.expand_dims(np.reshape(x_cut, (x_cut.shape[0],)), axis=0)
                x_cut = scaler.transform(x_cut)
                x_cut = np.reshape(x_cut, (x_cut.shape[0], x_cut.shape[1], 1))
                result = model.predict(x_cut)
                raw_detection, raw_event_type, raw_classification = self.postProcessing.processResult(result[0][0], result[1][0], result[2][0])
                events = self.postProcessing.suppressionMultiClass(raw_detection, raw_event_type, raw_classification)

                for ev in events:
                    ev[0][0] += i
                    # print(int(ev[0][0]), ev[0][1], int(ev[1][0]), ev[1][1], int(ev[2][0]), ev[2][1])
                    for window in windows:
                        #print(ev[0][0], window.initSample, window.initSample + round(SIGNAL_LENGTH / N_GRIDS))
                        if ev[0][0] >= window.initSample and ev[0][0] < window.initSample + round(self.m_signalBaseLength / self.m_ngrids):
                            if ev[2][0][1] >= 0.5:
                                window.add(ev)

                for window in windows:
                    window.move()

                if windows[0].isFinished():
                    ev = windows[0].compileResults()
                    if ev[1][0] == 0:
                        y_res[int(ev[0][0])] = 1
                    elif ev[1][0] == 1:
                        y_res[int(ev[0][0])] = -1

                    if ev[1][0] != 2:
                        title = title + str(int(ev[2][0])) + ", "
                    
                    windows.append(AnalysisWindow(windows[self.m_ngrids - 1].initSample + round(self.m_signalBaseLength / self.m_ngrids), config=self.m_configs))
                    del windows[0]
            
            # fig, ax = plt.subplots()
            # ax.set_title(title)
            # ax.plot(np.arange(0, x.shape[1]), x)
            # ax.plot(np.arange(0, x.shape[1]), ydet)
            # ax.plot(np.arange(0, x.shape[1]), y_res)

            title = title[:-2] + "]"

            plt.title(title)
            plt.plot(np.arange(0, x.shape[0]), x)
            plt.plot(np.arange(0, x.shape[0]), np.max(x) * 1.5 * ydet, label="Real event")
            plt.plot(np.arange(0, x.shape[0]), np.max(x) * y_res, label="Detected event")
            plt.xlabel("Samples")
            plt.ylabel("Current [A]")
            plt.legend(loc="upper right")