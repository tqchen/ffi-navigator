static auto registry =
    c10::RegisterOperators()
        .op("quantized::conv2d",
            c10::RegisterOperators::options().kernel<QConvInt8<2, false>>(
                TensorTypeId::QuantizedCPUTensorId))
        .op("quantized::conv2d_relu",
            c10::RegisterOperators::options().kernel<QConvInt8<2, true>>(
                TensorTypeId::QuantizedCPUTensorId))
        .op("quantized::conv3d",
            c10::RegisterOperators::options().kernel<QConvInt8<3, false>>(
                TensorTypeId::QuantizedCPUTensorId))
        .op("quantized::conv3d_relu",
            c10::RegisterOperators::options().kernel<QConvInt8<3, true>>(
                TensorTypeId::QuantizedCPUTensorId));
