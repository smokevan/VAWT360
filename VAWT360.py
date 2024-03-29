import adsk.core, adsk.fusion, adsk.cam, traceback
import math

# Global variables for application and UI
_app = adsk.core.Application.cast(None)
_ui = adsk.core.UserInterface.cast(None)

# Handler lists
_handlers = []

def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

        # Create a command definition
        cmdDef = _ui.commandDefinitions.itemById('createTurbine')
        if not cmdDef:
            cmdDef = _ui.commandDefinitions.addButtonDefinition('createTurbine', 'Create Turbine', 'Create a vertical axis wind turbine')

        # Connect to the command created event
        onCommandCreated = TurbineCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)

        # Execute the command
        cmdDef.execute()

        # Prevent script termination
        adsk.autoTerminate(False)
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class TurbineCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = adsk.core.CommandCreatedEventArgs.cast(args)
            inputs = cmd.command.commandInputs

            # Create a new group for drag turbine parameters
            dragTurbineParametersGroup = inputs.addGroupCommandInput('dragTurbineParameters', 'Drag Turbine Parameters')
            dragTurbineParametersInputs = dragTurbineParametersGroup.children

            dragTurbineParametersInputs.addValueInput('holeDiameter', 'Hole Diameter', 'in', adsk.core.ValueInput.createByString('1 in'))
            dragTurbineParametersInputs.addValueInput('shaftDiameter', 'Shaft Diameter', 'in', adsk.core.ValueInput.createByString('1 in'))
            dragTurbineParametersInputs.addValueInput('outerDiameter', 'Outer Diameter', 'in', adsk.core.ValueInput.createByString('10 in'))
            dragTurbineParametersInputs.addValueInput('bladeThickness', 'Blade Thickness', 'in', adsk.core.ValueInput.createByString('0.125 in'))
            dragTurbineParametersInputs.addValueInput('bladeDepth', 'Blade Depth', 'in', adsk.core.ValueInput.createByString('1 in'))
            dragTurbineParametersInputs.addValueInput('turbineHeight', 'Turbine Height', 'in', adsk.core.ValueInput.createByString('10 in'))
            dragTurbineParametersInputs.addIntegerSpinnerCommandInput('bladeCount', 'Blade Count', 1, 100, 1, 2)
            dragTurbineParametersInputs.addIntegerSpinnerCommandInput('twistCount', 'Twist Count', 1, 100, 1, 1)

            # Create a new group for airfoil turbine parameters
            airfoilTurbineParametersGroup = inputs.addGroupCommandInput('airfoilTurbineParameters', 'Airfoil Turbine Parameters')
            airfoilTurbineParametersInputs = airfoilTurbineParametersGroup.children

            airfoilTurbineParametersInputs.addStringValueInput('nacaProfile', 'NACA Profile', ('0015'))
            airfoilTurbineParametersInputs.addBoolValueInput('halfCosineSpacing', 'Half Cosine Spacing', True, '', True)
            airfoilTurbineParametersInputs.addIntegerSpinnerCommandInput('numPoints', 'Number of Points', 1, 100, 1, (100))
            airfoilTurbineParametersInputs.addBoolValueInput('finiteThicknessTE', 'Finite Thickness TE', True, '', False)
            airfoilTurbineParametersInputs.addIntegerSpinnerCommandInput('airfoilCount', 'Airfoil Count', 1, 100, 1, 3)
            airfoilTurbineParametersInputs.addValueInput('chordLength', 'Chord Length', 'in', adsk.core.ValueInput.createByString('3.0 in'))
            airfoilTurbineParametersInputs.addValueInput('distanceFromCenter', 'Distance from Center', 'in', adsk.core.ValueInput.createByString('15.0 in'))

            # Connect to command related events
            onExecute = TurbineCommandExecuteHandler()
            cmd.command.execute.add(onExecute)
            _handlers.append(onExecute)

            onDestroy = TurbineCommandDestroyHandler()
            cmd.command.destroy.add(onDestroy)
            _handlers.append(onDestroy)

        except Exception as e:
            _ui.messageBox('Failed to create command: {}'.format(str(e)))


class TurbineCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            inputs = eventArgs.command.commandInputs

            # Retrieve the groups
            dragTurbineParametersInputs = inputs.itemById('dragTurbineParameters').children
            airfoilTurbineParametersInputs = inputs.itemById('airfoilTurbineParameters').children

            # Retrieve and cast the input values to float for precision
            holeDiameter = float(dragTurbineParametersInputs.itemById('holeDiameter').value)
            shaftDiameter = float(dragTurbineParametersInputs.itemById('shaftDiameter').value)
            outerDiameter = float(dragTurbineParametersInputs.itemById('outerDiameter').value)
            bladeThickness = float(dragTurbineParametersInputs.itemById('bladeThickness').value)
            bladeDepth = float(dragTurbineParametersInputs.itemById('bladeDepth').value)
            turbineHeight = float(dragTurbineParametersInputs.itemById('turbineHeight').value)
            bladeCount = int(dragTurbineParametersInputs.itemById('bladeCount').value)  # Blade count is an integer

            # Retrieve and cast the airfoil parameters
            nacaProfile = airfoilTurbineParametersInputs.itemById('nacaProfile').value
            halfCosineSpacing = airfoilTurbineParametersInputs.itemById('halfCosineSpacing').value
            numPoints = int(airfoilTurbineParametersInputs.itemById('numPoints').value)
            finiteThicknessTE = airfoilTurbineParametersInputs.itemById('finiteThicknessTE').value
            airfoilCount = int(airfoilTurbineParametersInputs.itemById('airfoilCount').value)
            chordLength = float(airfoilTurbineParametersInputs.itemById('chordLength').value)
            distanceFromCenter = float(airfoilTurbineParametersInputs.itemById('distanceFromCenter').value)
            twistCount = int(dragTurbineParametersInputs.itemById('twistCount').value)  # Twist count is an integer

            # Create the turbine components
            createTurbine(holeDiameter, shaftDiameter, outerDiameter, bladeThickness, bladeDepth, turbineHeight, bladeCount, twistCount, nacaProfile, halfCosineSpacing, numPoints, finiteThicknessTE, chordLength, distanceFromCenter, airfoilCount)
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class TurbineCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        adsk.terminate()

def createTurbine(holeDiameter, shaftDiameter, outerDiameter, bladeThickness, bladeDepth, turbineHeight, bladeCount, twistCount, nacaProfile, halfCosineSpacing, numPoints, finiteThicknessTE, chordLength, distanceFromCenter, airfoilCount):
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        rootComp = design.rootComponent
        occs = rootComp.occurrences
        newOcc = occs.addNewComponent(adsk.core.Matrix3D.create())
        newComp = newOcc.component  
        # Now, use 'newComp' for all operations, like sketches, extrusions, etc.
        # For example, creating a sketch in the new component context
        sketches = newComp.sketches
        xzPlane = newComp.xZConstructionPlane
        sketch = sketches.add(xzPlane)

        # Create circles
        centerPoint = adsk.core.Point3D.create(0, 0, 0)
        holeCircle = sketch.sketchCurves.sketchCircles.addByCenterRadius(centerPoint, holeDiameter / 2.0)
        shaftCircle = sketch.sketchCurves.sketchCircles.addByCenterRadius(centerPoint, shaftDiameter / 2.0)

        # Existing circle creation for hole
        holeCircle = sketch.sketchCurves.sketchCircles.addByCenterRadius(centerPoint, holeDiameter / 2.0)

        # Calculate hexagon vertices and create an inscribed hexagon
        radius = holeDiameter / 2.0
        hexagonPoints = []
        for i in range(6):
            angle_deg = 60 * i - 30  # -30 to start the first point at the top
            angle_rad = math.radians(angle_deg)
            x = centerPoint.x + radius * math.cos(angle_rad)
            y = centerPoint.y + radius * math.sin(angle_rad)
            hexagonPoints.append(adsk.core.Point3D.create(x, y, 0))

        # Add sketch points for hexagon vertices
        sketchPoints = sketch.sketchPoints
        for point in hexagonPoints:
            sketchPoints.add(point)

        # Connect the hexagon points with lines
        for i in range(6):
            start_point = hexagonPoints[i]
            end_point = hexagonPoints[(i + 1) % 6]  # Wrap around to the first point after the last
            sketch.sketchCurves.sketchLines.addByTwoPoints(start_point, end_point)

       # Re-define the function to check if a profile is likely one of the six small profiles
        def is_small_hexagon_profile(profile, holeRadius):
            # Define the threshold as before
            area_threshold = math.pi * (holeRadius ** 2) / 6
            centroid = profile.areaProperties().centroid
            distance_from_center = math.sqrt(centroid.x**2 + centroid.y**2)
            return profile.areaProperties().area < area_threshold and distance_from_center < holeRadius

        # Initialize collection to hold profiles for extrusion
        profilesToExtrude = adsk.core.ObjectCollection.create()
        holeRadius = holeDiameter / 2.0
        shaftRadius = shaftDiameter / 2.0

        # First, add the disk profile between holeCircle and shaftCircle
        for profile in sketch.profiles:
            # This check assumes the profiles that are not small hexagon segments but are within the shaft circle
            # could include the desired disk profile. We distinguish it by not being one of the small profiles
            # and by being encircled by the shaft radius.
            centroid = profile.areaProperties().centroid
            distance_from_center = math.sqrt(centroid.x**2 + centroid.y**2)
            if distance_from_center < shaftRadius and not is_small_hexagon_profile(profile, holeRadius):
                profilesToExtrude.add(profile)
                break  # Assuming only one such profile exists, we break after adding it

        # Then, add the six small profiles between the hexagon and the holeCircle
        for profile in sketch.profiles:
            if is_small_hexagon_profile(profile, holeRadius):
                profilesToExtrude.add(profile)

        # Verify the expected number of profiles are selected
        if profilesToExtrude.count != 7:
            _ui.messageBox('Unexpected number of profiles selected for extrusion. Expected 7, found {}.'.format(profilesToExtrude.count))
            return

        # Perform the extrusion with the selected profiles
        extrudes = newComp.features.extrudeFeatures
        for profile in profilesToExtrude:
            extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.JoinFeatureOperation)
            extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(turbineHeight))
            extrude = extrudes.add(extrudeInput)

        arcPoint = adsk.core.Point3D.create((-(((((outerDiameter / 4.0) ** 2) / bladeDepth) + bladeDepth) / 2.0) + bladeDepth), (outerDiameter / 4.0), 0)
        sweepAngle = 2 * math.asin(outerDiameter / ((2 * ((outerDiameter / 4.0) ** 2) / bladeDepth) + bladeDepth))
        arc = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(arcPoint, centerPoint, sweepAngle)

        # Define the offset using BladeThickness
        offsetValue = adsk.core.ValueInput.createByReal(-bladeThickness)
        basePoint = arc.startSketchPoint.geometry  # Using the start point of the arc for the base point

        # Add the offset constraint to create offset arc
        geometricConstraints = sketch.geometricConstraints
        offsetConstraint = geometricConstraints.addOffset([arc], offsetValue, basePoint)

        if offsetConstraint and offsetConstraint.childCurves:
            offsetArc = offsetConstraint.childCurves[0]  # Assuming the first curve is the offset arc

            # Connect the end points of the original and the offset arc with a line
            sketch.sketchCurves.sketchLines.addByTwoPoints(arc.endSketchPoint, offsetArc.endSketchPoint)

        # Create a sketch on the XY plane for the vertical line
        sketchesXY = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        sketchXY = sketchesXY.add(xyPlane)

        # Calculate the end point of the vertical line based on turbineHeight
        startPoint = adsk.core.Point3D.create(0, 0, 0)  # Reusing the centerPoint as the start point for the vertical line
        endPoint = adsk.core.Point3D.create(0, turbineHeight, 0)  # n units up along the Y-axis

        # Add the vertical line to the sketch
        sketchXY.sketchCurves.sketchLines.addByTwoPoints(startPoint, endPoint)

                # Assume 'sketch' is already defined and contains your arcs and connecting line
        # Assume 'sketchXY' contains the vertical line for the sweep path

        # Step 1: Identify the profile formed by the two arcs and connecting line
        # This step is conceptual; you need to identify the correct profile in your sketch
        profileToSweep = sketch.profiles.item(7)  # Example: Selecting the first profile
        
        # Step 2: Create the path for the sweep
        # Assuming 'sketchXY' contains the vertical line for the path
        path = newComp.features.createPath(sketchXY.sketchCurves.sketchLines.item(0))  # Selecting the first line as the path

        # Step 3: Perform the sweep with the twist angle
        sweeps = newComp.features.sweepFeatures
        sweepInput = sweeps.createInput(profileToSweep, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        twistAngle = adsk.core.ValueInput.createByString(f"{(-360 / bladeCount)*twistCount} deg")
        sweepInput.twistAngle = twistAngle
        sweep = sweeps.add(sweepInput)

        # After creating the sweep feature for a blade
        sweepFeature = sweep  # Assuming 'sweep' is the variable holding the last created sweep feature

        # Collect the sweep feature in an ObjectCollection
        inputEntities = adsk.core.ObjectCollection.create()
        inputEntities.add(sweepFeature)

        # Get the Y axis as the axis of rotation for the circular pattern
        yAxis = newComp.yConstructionAxis

        # Create the circular pattern
        circularPatterns = newComp.features.circularPatternFeatures
        circularPatternInput = circularPatterns.createInput(inputEntities, yAxis)
        circularPatternInput.quantity = adsk.core.ValueInput.createByReal(bladeCount)
        circularPatternInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')  # Full circle
        circularPattern = circularPatterns.add(circularPatternInput)

        def naca4(number, n, finite_TE, half_cosine_spacing):
            m = int(number[0]) / 100.0  # Maximum camber
            p = int(number[1]) / 10.0   # Location of maximum camber
            t = int(number[2:]) / 100.0 # Maximum thickness
    
            # Define the thickness distribution function (same as before)
            def thickness(x):
                a0 = 0.2969
                a1 = -0.126
                a2 = -0.3516
                a3 = 0.2843
                a4 = -0.1015 if finite_TE else -0.1036  # Adjust for finite thickness at trailing edge
        
                return 5 * t * (a0 * math.sqrt(x) + a1 * x + a2 * x**2 + a3 * x**3 + a4 * x**4)
    
            # Define a function to calculate the camber line and its slope
            def camber_line(x):
                if x < p:
                    return m / p**2 * (2 * p * x - x**2)
                elif x == p:
                    return m
                else:
                    return m / (1 - p)**2 * ((1 - 2*p) + 2*p*x - x**2)
    
            def camber_slope(x):
                if x < p:
                    return (2*m / p**2) * (p - x)
                else:
                    return (2*m / (1 - p)**2) * (p - x)
    
            # Generate the x coordinates
            x = [i / n for i in range(n + 1)] if not half_cosine_spacing else [0.5 * (1 - math.cos(math.pi * i / n)) for i in range(n + 1)]
    
            # Calculate the camber line and its slope for each x
            yc = [camber_line(xi) for xi in x]
            dyc_dx = [camber_slope(xi) for xi in x]
            theta = [math.atan(dy) for dy in dyc_dx]
    
            # Calculate the thickness distribution for each x
            yt = [thickness(xi) for xi in x]
    
            # Calculate upper and lower surface points
            xu = [xi - yt[i] * math.sin(theta[i]) for i, xi in enumerate(x)]
            yu = [yc[i] + yt[i] * math.cos(theta[i]) for i in range(len(x))]
            xl = [xi + yt[i] * math.sin(theta[i]) for i, xi in enumerate(x)]
            yl = [yc[i] - yt[i] * math.cos(theta[i]) for i in range(len(x))]
    
            # Combine the upper and lower points
            X = xu + xl[::-1]
            Y = yu + yl[::-1]
    
            return X, Y

        # Method to Create Airfoil Sketch
        def createNacaAirfoil(nacaProfile, halfCosineSpacing, numPoints, finiteThicknessTE, chordLength, distanceFromCenter, turbineHeight, airfoilCount):
            app = adsk.core.Application.get()
            ui = app.userInterface
            design = app.activeProduct
            rootComp = design.rootComponent
            xzPlane = rootComp.xZConstructionPlane

            # Generate NACA airfoil points
            X, Z = naca4(nacaProfile, int(numPoints), finiteThicknessTE, halfCosineSpacing)

            # Adjust points based on chord length, center the airfoil, and position it for clockwise rotation
            points = []
            for x, z in zip(X, Z):
                # Flip the airfoil by reversing the x-coordinate around its central axis (chord/2)
                x_flipped = (chordLength / 2) - (x * chordLength - (chordLength / 2))
                z_shifted = turbineHeight / 2  # Position the airfoil at half the turbineHeight
                y_height = distanceFromCenter + (z * chordLength)  # Shift along the Y-axis for distanceFromCenter
                points.append(adsk.core.Point3D.create(x_flipped, y_height, z_shifted))

            # Create the sketch and connect points with lines
            sketches = rootComp.sketches
            sketch = sketches.add(xzPlane)
            # Here we ensure the points are connected in their original order to maintain the profile shape
            for i in range(len(points) - 1):
                sketch.sketchCurves.sketchLines.addByTwoPoints(points[i], points[i + 1])

            # Optionally, close the loop, connecting the last point back to the first
            sketch.sketchCurves.sketchLines.addByTwoPoints(points[-1], points[0])

            # Extrude the airfoil profile symmetrically
            extrudeDistance = (0.5 * turbineHeight + 1)  # Extrusion distance in mm
            profiles = sketch.profiles
            if profiles.count > 0:
                profileToExtrude = profiles.item(0)  # Assuming the airfoil profile is the only one in the sketch

                # Get the extrude features collection
                extrudes = rootComp.features.extrudeFeatures

                # Create an extrusion input to add to the collection
                extrudeInput = extrudes.createInput(profileToExtrude, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        
                # Set the extrusion distance symmetrically
                distance = adsk.core.ValueInput.createByString(f'{extrudeDistance} in')  # Half distance for symmetric extrusion
                extrudeInput.setSymmetricExtent(distance, True)
        
                # Create the extrusion
                extrudeFeature = extrudes.add(extrudeInput)

                # Assume extrudeFeature is the last created extrusion
            extrudeFeature = rootComp.features.extrudeFeatures.item(rootComp.features.extrudeFeatures.count - 1)

            # Create an ObjectCollection for the body/bodies produced by the extrusion
            bodiesCollection = adsk.core.ObjectCollection.create()
            for body in extrudeFeature.bodies:
                bodiesCollection.add(body)

            yAxis = newComp.yConyAxis = design.rootComponent.yConstructionAxis

            # Create the circular pattern
            circularPatterns = rootComp.features.circularPatternFeatures
            patternInput = circularPatterns.createInput(bodiesCollection, yAxis)
            patternInput.quantity = adsk.core.ValueInput.createByReal(airfoilCount)
            patternInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')  # Distribute around a full circle
            patternInput.isSymmetric = False  # Adjust if your design requires symmetric distribution

            # Create the pattern
            circularPatternFeature = circularPatterns.add(patternInput)

        createNacaAirfoil(nacaProfile, halfCosineSpacing, numPoints, finiteThicknessTE, chordLength, distanceFromCenter, turbineHeight, airfoilCount)
      
    except Exception as e:
        ui = adsk.core.Application.get().userInterface
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:
        if _ui:
            for handler in _handlers:
                _ui.messageBox(str(handler))
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))