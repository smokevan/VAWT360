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
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command
            inputs = cmd.commandInputs

            # Add inputs for turbine parameters
            inputs.addValueInput('holeDiameter', 'Hole Diameter (mm)', 'mm', adsk.core.ValueInput.createByReal(3.0))
            inputs.addValueInput('shaftDiameter', 'Shaft Diameter (mm)', 'mm', adsk.core.ValueInput.createByReal(4.0))
            inputs.addValueInput('outerDiameter', 'Outer Diameter (mm)', 'mm', adsk.core.ValueInput.createByReal(12.0))
            inputs.addValueInput('bladeThickness', 'Blade Thickness (mm)', 'mm', adsk.core.ValueInput.createByReal(0.5))
            inputs.addValueInput('bladeDepth', 'Blade Depth (mm)', 'mm', adsk.core.ValueInput.createByReal(0.5))
            inputs.addValueInput('turbineHeight', 'Turbine Height (mm)', 'mm', adsk.core.ValueInput.createByReal(20.0))
            inputs.addIntegerSpinnerCommandInput('bladeCount', 'Blade Count', 1, 100, 1, 2)
            inputs.addIntegerSpinnerCommandInput('twistCount', 'Twist Count', 1, 100, 1, 1)

            # Connect to command related events
            onExecute = TurbineCommandExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)

            onDestroy = TurbineCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
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

            # Retrieve and cast the input values to float for precision
            holeDiameter = float(inputs.itemById('holeDiameter').value)
            shaftDiameter = float(inputs.itemById('shaftDiameter').value)
            outerDiameter = float(inputs.itemById('outerDiameter').value)
            bladeThickness = float(inputs.itemById('bladeThickness').value)
            bladeDepth = float(inputs.itemById('bladeDepth').value)
            turbineHeight = float(inputs.itemById('turbineHeight').value)
            bladeCount = int(inputs.itemById('bladeCount').value)  # Blade count is an integer
            twistCount = int (inputs.itemById('twistCount').value)

            # Create the turbine components
            createTurbine(holeDiameter, shaftDiameter, outerDiameter, bladeThickness, bladeDepth, turbineHeight, bladeCount, twistCount)
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class TurbineCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        adsk.terminate()

def createTurbine(holeDiameter, shaftDiameter, outerDiameter, bladeThickness, bladeDepth, turbineHeight, bladeCount, twistCount):
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