import React from 'react';

const LitReview = ({ isOpen, onClose }) => {
    if (!isOpen) return null;

    return (
        <div className="lit-review-overlay">
            <div className="lit-review-modal">
                <div className="lit-review-header">
                    <h2>Chapter 2: Literature Review</h2>
                    <button className="close-btn" onClick={onClose}>&times;</button>
                </div>
                <div className="lit-review-content">
                    <section>
                        <h3>2.1 Introduction</h3>
                        <p>
                            The literature review covers the existing literature on flood prediction, rainfall forecasting, applications of machine learning in hydrology, geospatial modeling of floods, and flood visualization web-based systems.
                        </p>
                    </section>

                    <section>
                        <h3>2.3 Traditional Flood Prediction and Modeling Approaches</h3>
                        <p>
                            Traditional flood prediction systems rely primarily on physically based hydrological and hydraulic models. Hydrological models simulate rainfall–runoff processes, while hydraulic models simulate water flow through river channels and floodplains.
                        </p>
                        <ul>
                            <li>Hydrologic Engineering Center models</li>
                            <li>Storm Water Management Model (SWMM)</li>
                            <li>MIKE FLOOD</li>
                        </ul>
                        <p><strong>Limitations:</strong> High dependency on dense sensor networks, significant computational complexity, and limited adaptability to changing climatic conditions.</p>
                    </section>

                    <section>
                        <h3>2.5 Machine Learning in Flood and Rainfall Prediction</h3>
                        <p>
                            Machine learning has gained significant attention in hydrology due to its ability to model complex nonlinear relationships. Unlike physically based models, machine learning approaches do not require explicit representation of physical processes.
                        </p>
                        <p><strong>Advantages:</strong> Reduced reliance on physical parameters, faster computation after training, and strong performance with limited data.</p>
                    </section>

                    <section>
                        <h3>2.18 Comparative Summary of Flood Prediction Approaches</h3>
                        <div className="table-container">
                            <table className="comparison-table">
                                <thead>
                                    <tr>
                                        <th>Approach</th>
                                        <th>Data Requirements</th>
                                        <th>Computational Cost</th>
                                        <th>Scalability</th>
                                        <th>Data-Scarce Suitability</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td className="bold">Physically Based</td>
                                        <td>High (Soil, Geometry)</td>
                                        <td>Very High</td>
                                        <td>Low</td>
                                        <td className="red">Poor</td>
                                    </tr>
                                    <tr>
                                        <td className="bold">Statistical</td>
                                        <td>Medium (Historical)</td>
                                        <td>Low</td>
                                        <td>Medium</td>
                                        <td className="orange">Fair</td>
                                    </tr>
                                    <tr>
                                        <td className="bold">Machine Learning</td>
                                        <td>Medium (Weather)</td>
                                        <td>Low (Inference)</td>
                                        <td>High</td>
                                        <td className="green">Excellent</td>
                                    </tr>
                                    <tr>
                                        <td className="bold">Hybrid</td>
                                        <td>High</td>
                                        <td>High</td>
                                        <td>Medium</td>
                                        <td className="orange">Medium</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </section>

                    <section>
                        <h3>2.20 Summary</h3>
                        <p>
                            This chapter reviewed existing research on flood prediction, rainfall forecasting, machine learning applications, geospatial modeling, and web-based visualization systems. The identified research gaps provide a clear justification for the methodology and system architecture presented in this application.
                        </p>
                    </section>
                </div>
            </div>
        </div>
    );
};

export default LitReview;
