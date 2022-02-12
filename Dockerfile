FROM python:3.9
# MAINTAINER Lee Cooper <lee.cooper@northwestern.edu>

RUN pip install --pre girder-slicer-cli-web
RUN pip install girder-client

RUN pip install openslide-python==1.1.2 scikit-image==0.18.1 scikit-learn==0.24.1 numpy==1.20.1 scipy==1.6.1 matplotlib==3.3.4
RUN pip install dill==0.3.3 pytest importlib-resources


RUN apt update && apt install -y openslide-tools
RUN pip install numpy --upgrade

RUN pip install imageio
RUN pip install large-image
RUN pip install large-image-source-openslide




COPY . $PWD
ENTRYPOINT ["python", "./cli_list.py"]
