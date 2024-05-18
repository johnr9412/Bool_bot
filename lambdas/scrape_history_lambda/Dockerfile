FROM public.ecr.aws/lambda/python:3.12
RUN microdnf install gcc g++ gtk3 git -y
RUN pip install requests
RUN pip install git+https://github.com/capless/warrant.git@fc9a04a4806f947db73e734a6fe8eff4d00666a0
COPY step_scrape.py ./
CMD [ "step_scrape.lambda_handler" ]
