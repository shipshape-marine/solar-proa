# Navigate to the current directory
cd docs

# Install all 3 options
ridk install
# If does not work, download MSYS2 from https://www.msys2.org/ then retry

# Install dependencies
bundle install

# Run Jekyll locally
bundle exec jekyll serve

# Open in browser
open http://localhost:4000/CAD/

