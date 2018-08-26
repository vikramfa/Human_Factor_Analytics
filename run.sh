#!/bin/bash
nameko run --config nameko.yml services.DataPublishService services.EARService services.ImagePublishService services.ImagePublishService2 services.HeartRateService services.GenderService services.EmotionService services.HeadPositionService&
python earapp.py
python hrapp.py
python emotionapp.py