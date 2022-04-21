FROM public.ecr.aws/lambda/python:3.8
RUN pip install requests
RUN pip install pandas
COPY get_schedule_lambda.py ./
COPY methods ./
COPY methods/* ./methods/
CMD [ "get_schedule_lambda.lambda_handler" ]
