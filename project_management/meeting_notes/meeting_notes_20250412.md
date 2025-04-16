# Meeting Notes: runctl Project Discussion
*Date: April 12, 2025*

## Initial Project Concept Discussion

**Assistant**  
I'll help you create a new PRD following the example structure. Let's start by gathering some key information about your project.

To create a meaningful PRD, I'll need to understand:
- What product/application you want to build
- The main problem it solves
- Who the target users are

Could you please provide these basic details so I can help you craft a well-structured PRD that follows the template format? Once you share those details, I can help you:
- Structure the overview section
- Define core features
- Map out the user experience
- Plan the technical architecture
- Create a logical development roadmap
- Identify potential risks and mitigations

Please share the basic concept of your product/application, and I'll help you develop it into a comprehensive PRD.

**User:**  
Thank you! Let's chat about the project some more before working on the PRD. It is called runctl (let me know if you think this is a bad name). It is a CLI/TUI running analytics app for software engineers who only love running as much as the terminal.

The problem that gave me the idea for the app is inaccurate heart rate values in my running data that I wanted to clean before uploading to Garmin/Strava. But then I thought that it would be cool to build a fully featured running analytics app that runs in the terminal, where users can:
- Upload running data
- Clean the data
- Upload to Strava
- Store data (local/cloud?) for analysis
- View a TUI dashboard showing progress, fitness, target races, etc.
- Generate training plans and workouts
- Interact with an AI running coach in the terminal

## Project Analysis and Feedback

**Assistant:**  
This is a fantastic idea! I love the concept of combining running analytics with a terminal-based interface, especially targeting software engineers who appreciate command-line tools. The name "runctl" is actually quite fitting - it follows the Unix/Linux naming convention (like kubectl, systemctl) which your target audience will immediately recognize.

Let me break down the key aspects of your idea and add some thoughts:

### Core Value Proposition
- Terminal-based running analytics platform for tech-savvy runners
- Data cleaning/preprocessing before syncing with popular platforms
- Advanced analytics with a developer-friendly interface
- AI-powered running coach in the terminal

### Key Differentiators
- Terminal-first approach (unique in the running app space)
- Focus on data quality and preprocessing
- Integration with existing platforms rather than replacing them
- Technical user experience optimized for developers

### Potential Features
1. **Data Import/Export**
   - Import from various fitness devices/formats (FIT, GPX, TCX)
   - Smart data cleaning (HR anomalies, GPS smoothing)
   - Sync with Strava/Garmin

2. **Analytics Dashboard (TUI)**
   - Real-time stats visualization using terminal graphics
   - Training load/fitness trends
   - Race predictions and performance metrics
   - Custom metric tracking

3. **Training Management**
   - Training plan generation
   - Workout scheduling and tracking
   - Race goal setting and progress monitoring

4. **AI Coach Integration**
   - Natural language interaction in terminal
   - Training plan adjustments
   - Performance analysis
   - Nutrition and recovery advice

### Technical Considerations
- Local-first architecture with optional cloud sync
- Efficient data storage for quick terminal rendering
- Extensible plugin system for additional data sources
- Clean, maintainable TUI framework

## Project Scope Discussion

**Assistant:**  
Before we dive into the PRD, I have a few questions to help focus the scope:

1. **For the MVP, should we prioritize:**
   - Data cleaning and Strava sync features, or
   - The TUI dashboard and analytics, or
   - The AI coaching functionality?

2. **Regarding data storage:**
   - Do you want to start with local-only storage?
   - Should cloud sync be part of the initial release?

3. **For the AI coaching feature:**
   - Should it be a core feature or a premium add-on?
   - Any specific aspects of coaching you want to focus on?

4. **About the TUI dashboard:**
   - What key metrics would you want to see at a glance?
   - How important is real-time data visualization vs. text-based summaries?

## Portfolio Project Discussion

**User:**  
I forgot to mention before that I am an aspiring data engineer. What do you think about making this my main portfolio project, and integrating the data lifecycle, ETL/ELT, and data engineering tools etc? Or should this be a separate project with the goal of getting subscribers and generating revenue?

**Assistant:**  
This is an excellent question! The project actually has great potential for both paths - as a portfolio piece for data engineering and as a commercial product.

### As a Data Engineering Portfolio Project

#### Data Pipeline Showcase
- Ingest: Multiple data formats (FIT, GPX, TCX) from various sources
- Transform: Complex data cleaning, normalization, and enrichment
- Load: Structured storage and analytics-ready formats
- Real-time vs. Batch processing demonstrations

#### Modern Data Stack Integration
- dbt for data transformations
- Airflow/Dagster for pipeline orchestration
- Data quality testing and monitoring
- Data versioning and lineage tracking

#### Technical Highlights
- Stream processing for real-time metrics
- Data modeling for time-series analytics
- API development and integration
- Performance optimization for large datasets

#### Architecture Patterns
- Event-driven architecture
- Data mesh principles
- Lambda/Kappa architecture
- CQRS pattern for read/write optimization

### As a Commercial Product

#### Revenue Streams
- Freemium model (basic features free, advanced analytics paid)
- AI coaching as a premium feature
- Cloud storage and sync capabilities
- Custom training plan generation

#### Market Focus
- Target developer-athletes specifically
- Focus on data privacy and ownership
- Emphasis on customization and extensibility
- Integration with existing platforms

### Recommendation

I would suggest starting this as a data engineering portfolio project for several reasons:

#### Perfect Learning Platform
- Demonstrates end-to-end data engineering skills
- Covers both streaming and batch processing
- Includes real-world data cleaning challenges
- Shows ability to handle time-series data

#### Career Impact
- Showcases modern data stack expertise
- Demonstrates domain knowledge application
- Shows ability to build production-grade systems
- Highlights both technical and product thinking

#### Future Flexibility
- Can evolve into a commercial product later
- Great for blog posts and technical writing
- Potential for open-source contributions
- Could become a case study for interviews

## Project Evolution Discussion

**User:**  
Love it! Thank you! Let's talk about structuring for max portfolio impact. The narrative that I am thinking about using in interviews is that what got me into programming was creating the Python script that cleans heart rate data. So in order to follow the narrative, I am thinking about starting with that simple script and building from there. What do you think?

**Assistant:**  
That's a brilliant narrative approach! Starting with the heart rate data cleaning script creates a compelling story of organic growth and problem-solving that interviewers will love. It demonstrates:
- Personal Motivation - Shows you're building solutions to real problems
- Technical Evolution - Illustrates your growth from scripts to production systems
- Engineering Journey - Perfect representation of how simple solutions evolve into robust systems

Let's outline how we could structure this evolution to maximize portfolio impact:

### Phase 1: The Origin Story (The Script)
- Simple Python script for HR data cleaning
- Basic statistical methods for anomaly detection
- Command line arguments for file input
- Clear documentation of the problem and solution
- Unit tests for cleaning logic

```python
# Example narrative in code comments:
"""
I noticed my heart rate data had impossible spikes during runs.
This script uses statistical methods to identify and clean these anomalies,
ensuring more accurate training data for analysis.
"""
```

### Phase 2: Engineering Best Practices
- Refactor into proper package structure
- Add logging and error handling
- Implement configuration management
- Expand test coverage
- Add CI/CD pipeline
- Create documentation

### Phase 3: Data Engineering Foundations
- Implement proper ETL structure
- Add support for multiple data formats
- Introduce data validation
- Set up basic data storage
- Add simple metrics calculation
- Create basic CLI interface

### Phase 4: Advanced Data Platform
- Implement streaming data processing
- Add data warehouse integration
- Create data quality monitoring
- Implement metadata management
- Add basic TUI dashboard
- Set up orchestration

### Phase 5: Production-Grade Features
- Implement advanced analytics
- Add machine learning components
- Create API layer
- Implement advanced TUI
- Add cloud integration options
- Implement advanced monitoring

### Portfolio Storytelling Elements

#### Documentation at Each Phase
- Technical decisions and their rationale
- Architecture diagrams
- Performance improvements
- Lessons learned

#### GitHub Structure
- Clear commit history showing evolution
- Detailed PRs explaining changes
- Project boards showing planning
- Comprehensive README updates

#### Technical Blog Posts
- "From Script to System: Building a Data Platform"
- "Scaling a Personal Project with Data Engineering Best Practices"
- "Implementing Real-time Analytics in a CLI Tool"

#### Interview Talking Points
```
"It started with a simple problem: my heart rate data was inaccurate.
I wrote a Python script to clean it, but then I saw an opportunity to
apply data engineering principles to create something more robust..."
```

#### Key Technical Demonstrations
- Data quality management
- Performance optimization
- System scaling
- Real-time processing
- Data modeling
- API design

## Project Scope Refinement

**User:**  
A couple quick questions: What is the reasoning behind multiformat support? And can we add the Strava integration to Phase 1 if that doesn't mess with the overall plan? I forgot to mention that in the narrative. It should be something like this: "I needed to clean inaccurate heart rate data before uploading to Strava."

**Assistant:**  
Great questions! Let me address both:

### Multi-format Support Reasoning
Currently, this might be more complexity than we need early on. I included it thinking about different data sources, but you're right - we should focus on the specific format you're working with. Most likely, if you're uploading to Strava, you're dealing with FIT files (the most common format for modern fitness devices). We can always add support for GPX and TCX later if needed.

### Adding Strava Integration to Phase 1
Yes! This actually makes the narrative even stronger. It creates a complete, useful workflow right from Phase 1: "Clean HR data → Upload to Strava." This is a perfect MVP that solves a real problem and sets us up for future expansion.

These changes make the project progression more focused and logical:

- Phase 1 now tells a complete story:
  - Problem: "I have inaccurate heart rate data in my FIT files"
  - Solution: "Clean the data before uploading to Strava"
  - Result: A useful tool that solves a specific problem

- Future Phases maintain the data engineering evolution:
  - Start with a focused solution (FIT files + Strava)
  - Expand to more formats when needed
  - Add more sophisticated data engineering features

This creates a better narrative for your portfolio:
- Shows how you identified and solved a specific problem
- Demonstrates integration with external APIs early
- Establishes a foundation for showcasing data engineering skills
- Creates a clearer progression from script to platform
