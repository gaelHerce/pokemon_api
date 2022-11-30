FROM python:3.10 
# Or any preferred Python version.
ADD player.py .
ADD resolvers.py .
ADD player.graphql .
ADD db/database.db .
ADD db/init.sql .
RUN pip install requests beautifulsoup4 python-dotenv ariadne flask resolver uuid
CMD ["python", "./player.py"] 