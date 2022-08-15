FROM public.ecr.aws/lambda/python:3.8
RUN pip install spotipy
COPY get_albums_lambda.py ./
COPY methods ./
COPY methods/* ./methods/
CMD [ "get_albums_lambda.lambda_handler" ]
