class Conv2d(_ConvNd):
    _FLOAT_MODULE = nn.Conv2d

    def __init__(self, in_channels, out_channels, kernel_size, stride=1,
                 padding=0, dilation=1, groups=1, bias=True,
                 padding_mode='zeros'):
        kernel_size = _pair(kernel_size)
        stride = _pair(stride)
        padding = _pair(padding)
        dilation = _pair(dilation)
        super(Conv2d, self).__init__(
            in_channels, out_channels, kernel_size, stride, padding, dilation,
            groups, bias, padding_mode)

    def _get_name(self):
        return 'QuantizedConv2d'

    def set_weight_bias(self, w, b):
        # type: (torch.Tensor, Optional[torch.Tensor]) -> None
        self._packed_params = torch.ops.quantized.conv2d_prepack(
            w, b, self.stride, self.padding, self.dilation, self.groups)

    def _weight_bias(self):
        return torch.ops.quantized.conv2d_unpack(self._packed_params)

    def weight(self):
        (w, _) = torch.ops.quantized.conv2d_unpack(self._packed_params)
        return w

    def bias(self):
        (_, b) = torch.ops.quantized.conv2d_unpack(self._packed_params)
        return b

    def forward(self, input):
        # Temporarily using len(shape) instead of ndim due to JIT issue
        # https://github.com/pytorch/pytorch/issues/23890
        if len(input.shape) != 4:
            raise ValueError("Input shape must be `(N, C, H, W)`!")
        return ops.quantized.conv2d(
            input, self._packed_params, self.stride, self.padding,
            self.dilation, self.groups, self.scale, self.zero_point)
