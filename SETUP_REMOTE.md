# Setting Up Remote Repository

This guide shows how to push the mat2h5 repository to GitHub or GitLab.

## GitHub

### 1. Create a new repository on GitHub
- Go to https://github.com/new
- Name it `mat2h5` (or your preferred name)
- **Do NOT** initialize with README, .gitignore, or license (we already have these)
- Click "Create repository"

### 2. Add remote and push

```bash
cd /path/to/mat2h5
git remote add origin https://github.com/YOUR_USERNAME/mat2h5.git
git branch -M main
git push -u origin main
```

Or if using SSH:
```bash
git remote add origin git@github.com:YOUR_USERNAME/mat2h5.git
git branch -M main
git push -u origin main
```

## GitLab

### 1. Create a new project on GitLab
- Go to https://gitlab.com/projects/new
- Name it `mat2h5`
- Set visibility (public/private)
- **Do NOT** initialize with README
- Click "Create project"

### 2. Add remote and push

```bash
cd /path/to/mat2h5
git remote add origin https://gitlab.com/YOUR_USERNAME/mat2h5.git
git branch -M main
git push -u origin main
```

Or if using SSH:
```bash
git remote add origin git@gitlab.com:YOUR_USERNAME/mat2h5.git
git branch -M main
git push -u origin main
```

## Verify

After pushing, verify the remote is set up correctly:

```bash
git remote -v
```

You should see:
```
origin  https://github.com/YOUR_USERNAME/mat2h5.git (fetch)
origin  https://github.com/YOUR_USERNAME/mat2h5.git (push)
```

## Future Updates

After setting up the remote, you can push future changes with:

```bash
git add .
git commit -m "Your commit message"
git push
```

