FROM public.ecr.aws/lambda/python:3.8
RUN yum install gcc g++ gtk3 -y
RUN pip install requests
RUN pip install warrant
COPY step_scrape.py ./
CMD [ "step_scrape.lambda_handler" ]
