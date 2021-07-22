import numpy as np
import torch.nn as nn
import torch
import torch.nn.functional as F

from torchlibrosa.stft import magphase


def init_embedding(layer):
    """Initialize a Linear or Convolutional layer."""
    nn.init.uniform_(layer.weight, -1.0, 1.0)

    if hasattr(layer, 'bias'):
        if layer.bias is not None:
            layer.bias.data.fill_(0.0)


def init_layer(layer):
    """Initialize a Linear or Convolutional layer."""
    nn.init.xavier_uniform_(layer.weight)

    if hasattr(layer, "bias"):
        if layer.bias is not None:
            layer.bias.data.fill_(0.0)


def init_bn(bn):
    """Initialize a Batchnorm layer."""
    bn.bias.data.fill_(0.0)
    bn.weight.data.fill_(1.0)


def act(x, activation):
    if activation == "relu":
        return F.relu_(x)

    elif activation == "leaky_relu":
        return F.leaky_relu_(x, negative_slope=0.01)

    elif activation == "swish":
        return x * torch.sigmoid(x)

    else:
        raise Exception("Incorrect activation!")


class Base:
    def __init__(self):
        pass

    def spectrogram(self, input, eps=0.0):
        (real, imag) = self.stft(input)
        return torch.clamp(real ** 2 + imag ** 2, eps, np.inf) ** 0.5

    def spectrogram_phase(self, input, eps=0.0):
        (real, imag) = self.stft(input)
        mag = torch.clamp(real ** 2 + imag ** 2, eps, np.inf) ** 0.5
        cos = real / mag
        sin = imag / mag
        return mag, cos, sin

    '''
    def wav_to_spectrogram_phase(self, input, eps=1e-10):
        """Waveform to spectrogram.

        Args:
          input: (batch_size, channels_num, segment_samples)

        Outputs:
          output: (batch_size, channels_num, time_steps, freq_bins)
        """
        sp_list = []
        cos_list = []
        sin_list = []
        channels_num = input.shape[1]
        for channel in range(channels_num):
            mag, cos, sin = self.spectrogram_phase(input[:, channel, :], eps=eps)
            sp_list.append(mag)
            cos_list.append(cos)
            sin_list.append(sin)

        sps = torch.cat(sp_list, dim=1)
        coss = torch.cat(cos_list, dim=1)
        sins = torch.cat(sin_list, dim=1)
        return sps, coss, sins
    '''

    def wav_to_spectrogram_phase(self, input, eps=1e-10):
        """Waveform to spectrogram.

        Args:
          input: (batch_size, channels_num, segment_samples)

        Outputs:
          output: (batch_size, channels_num, time_steps, freq_bins)
        """

        batch_size, channels_num, segment_samples = input.shape

        # Reshape input because the following spectrogram function requires
        # input size of (n, segments_num)
        x = input.reshape(batch_size * channels_num, segment_samples)

        sps, coss, sins = self.spectrogram_phase(x, eps=eps)

        _, _, time_steps, freq_bins = sps.shape
        sps = sps.reshape(batch_size, channels_num, time_steps, freq_bins)
        coss = coss.reshape(batch_size, channels_num, time_steps, freq_bins)
        sins = sins.reshape(batch_size, channels_num, time_steps, freq_bins)

        return sps, coss, sins

    '''
    def wav_to_spectrogram(self, input, eps=0.0):
        """Waveform to spectrogram.

        Args:
          input: (batch_size, channels_num, segment_samples)

        Outputs:
          output: (batch_size, channels_num, time_steps, freq_bins)
        """
        sp_list = []
        channels_num = input.shape[1]
        for channel in range(channels_num):
            sp_list.append(self.spectrogram(input[:, channel, :], eps=eps))

        output = torch.cat(sp_list, dim=1)
        return output
    '''

    '''
    def spectrogram_to_wav(self, input, spectrogram, length=None):
        """Spectrogram to waveform.

        Args:
          input: (batch_size, segment_samples, channels_num)
          spectrogram: (batch_size, channels_num, time_steps, freq_bins)

        Outputs:
          output: (batch_size, channels_num, segment_samples)
        """
        channels_num = input.shape[1]
        wav_list = []
        for channel in range(channels_num):
            (real, imag) = self.stft(input[:, channel, :])
            (_, cos, sin) = magphase(real, imag)
            wav_list.append(
                self.istft(
                    spectrogram[:, channel : channel + 1, :, :] * cos,
                    spectrogram[:, channel : channel + 1, :, :] * sin,
                    length,
                )
            )

        output = torch.stack(wav_list, dim=1)
        return output
    '''


class Subband:
    def __init__(self, subbands_num):
        self.subbands_num = subbands_num

    def analysis(self, x):
        r"""Split time-frequency representation into subbands. Stack the
        subbands to the channel dimension.

        Args:
            x: (batch_size, channels_num, time_steps, freq_bins)

        Returns:
            output: (batch_size, channels_num * subbands_num, time_steps, freq_bins // subbands_num)
        """
        batch_size, channels_num, time_steps, freq_bins = x.shape

        x = x.reshape(
            batch_size,
            channels_num,
            time_steps,
            self.subbands_num,
            freq_bins // self.subbands_num,
        )
        x = x.transpose(2, 3)
        output = x.reshape(
            batch_size,
            channels_num * self.subbands_num,
            time_steps,
            freq_bins // self.subbands_num,
        )

        return output

    def synthesis(self, x):
        r"""Synthesis subband time-frequency representations into original
        time-frequency representation.

        Args:
            x: (batch_size, channels_num * subbands_num, time_steps, freq_bins // subbands_num)

        Returns:
            output: (batch_size, channels_num, time_steps, freq_bins)
        """

        batch_size, subband_channels_num, time_steps, subband_freq_bins = x.shape

        channels_num = subband_channels_num // self.subbands_num
        freq_bins = subband_freq_bins * self.subbands_num

        x = x.reshape(
            batch_size,
            channels_num,
            self.subbands_num,
            time_steps,
            freq_bins // self.subbands_num,
        )
        x = x.transpose(2, 3)
        output = x.reshape(batch_size, channels_num, time_steps, freq_bins)

        return output
