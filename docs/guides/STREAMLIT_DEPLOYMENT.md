# 🚀 Streamlit Cloud Deployment Guide

## Quick Deploy to Streamlit Cloud

### 1. Prerequisites
- GitHub repository with dashboard code
- Streamlit Cloud account (free at share.streamlit.io)
- Repository must be public or you have Pro account

### 2. Deployment Steps

1. **Connect to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io/)
   - Click "Deploy an app"
   - Connect your GitHub account
   - Select repository: `AndreaBozzo/Osservatorio`
   - Set branch: `main` or `feature/dashboard`
   - Set main file path: `dashboard/app.py`

2. **Advanced Settings**
   - Python version: `3.9` or `3.10`
   - Requirements file: `dashboard/requirements.txt`
   - Secrets: Add any environment variables if needed

3. **Deploy**
   - Click "Deploy!"
   - Wait for deployment to complete
   - Your app will be available at: `https://YOUR-REPO-NAME.streamlit.app`

### 3. App Configuration

#### Streamlit Config (`.streamlit/config.toml`):
```toml
[theme]
primaryColor = "#0066CC"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
enableCORS = false
port = 8501
maxUploadSize = 200

[browser]
gatherUsageStats = false

[logger]
level = "info"
```

#### Dependencies (`dashboard/requirements.txt`):
```txt
streamlit>=1.32.0
plotly>=5.17.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
openpyxl>=3.1.0
pyarrow>=13.0.0
requests>=2.31.0
loguru>=0.7.0
python-dotenv>=1.0.0
lxml>=4.9.0
```

### 4. Expected App Features

✅ **Working Features:**
- Interactive dashboard with 6 categories
- Sample data visualization
- Responsive layout
- Filter system
- Export functionality (basic)
- Real-time metrics

🔄 **In Development:**
- Live ISTAT data integration
- Advanced filtering
- Data export formats
- User authentication
- API endpoints

### 5. Monitoring

#### App Health Check:
- Dashboard loads without errors
- Sample data displays correctly
- Interactive elements work
- Responsive on mobile

#### Performance Metrics:
- Load time: <5 seconds
- Memory usage: <1GB
- CPU usage: <50%
- Error rate: <1%

### 6. Troubleshooting

#### Common Issues:

1. **Import Errors**:
   - Check `requirements.txt` includes all dependencies
   - Verify Python version compatibility
   - Use fallback imports in app.py

2. **Data Loading Issues**:
   - App uses sample data when real data not available
   - Check data directory structure
   - Verify file permissions

3. **Performance Issues**:
   - Enable caching with `@st.cache_data`
   - Optimize data loading
   - Use lazy loading for large datasets

#### Debug Mode:
```bash
# Run locally for debugging
streamlit run dashboard/app.py --server.enableCORS false
```

### 7. Post-Deployment

1. **Test the deployed app**:
   - Navigate to your Streamlit Cloud URL
   - Test all dashboard features
   - Verify responsive design
   - Check performance metrics

2. **Monitor deployment**:
   - Check Streamlit Cloud logs
   - Monitor app performance
   - Track user analytics

3. **Update deployment**:
   - Push changes to GitHub
   - Streamlit Cloud auto-deploys from main branch
   - Monitor deployment status

### 8. Security Considerations

- No sensitive data in repository
- Use Streamlit secrets for API keys
- Enable HTTPS (automatic on Streamlit Cloud)
- Rate limiting implemented
- Input validation active

### 9. Expected URLs

- **Production**: `https://osservatorio-istat.streamlit.app`
- **Development**: `https://osservatorio-istat-dev.streamlit.app`
- **Local**: `http://localhost:8501`

### 10. Success Metrics

- ✅ App deploys successfully
- ✅ All dashboard tabs load
- ✅ Sample data displays
- ✅ Interactive elements work
- ✅ Mobile responsive
- ✅ Load time <5s
- ✅ No critical errors

---

**Next Steps After Deployment:**
1. Test all functionality
2. Monitor performance
3. Collect user feedback
4. Iterate and improve
5. Add more data sources
6. Implement advanced features

**Support:**
- GitHub Issues: [Report bugs](https://github.com/AndreaBozzo/Osservatorio/issues)
- Documentation: [README](https://github.com/AndreaBozzo/Osservatorio/blob/main/README.md)
- Streamlit Docs: [Official documentation](https://docs.streamlit.io/)

